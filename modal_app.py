import os
import json
import base64
import tempfile
import urllib.request
import urllib.error
import asyncio

import modal

app = modal.App("cat-inspect-ai-sprint1")

# Shared volume where the fine-tuned LoRA adapter lives (written by pipeline.py)
adapter_volume = modal.Volume.from_name("d6n-training-vault", create_if_missing=False)
ADAPTER_PROD      = "/data/adapters/production/v1"
BASE_MODEL        = "mistralai/Mistral-7B-Instruct-v0.2"
MODEL_CACHE_DIR   = "/data/models/mistral-7b"

image = modal.Image.debian_slim().apt_install("ffmpeg").pip_install(
    "openai-whisper", "transformers", "torch", "pillow", "accelerate"
)

# Heavier image used by the fine-tuned model inference function
adapter_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(["torch", "transformers", "peft", "accelerate", "bitsandbytes"])
)

D6N_PARTS = {
    "track":         "PT-D6N-TRK-001",
    "blade":         "PT-D6N-BLD-002",
    "hydraulic":     "PT-D6N-HYD-003",
    "engine":        "PT-D6N-ENG-004",
    "final drive":   "PT-D6N-FDR-005",
    "undercarriage": "PT-D6N-UND-006",
    "sprocket":      "PT-D6N-SPR-007",
    "idler":         "PT-D6N-IDL-008",
    "roller":        "PT-D6N-RLR-009",
    "cutting edge":  "PT-D6N-CTE-010",
    "cooling hose":  "PT-D6N-CLH-011",
    "radiator":      "PT-D6N-RAD-012",
    "step":          "PT-D6N-STP-013",
    "handrail":      "PT-D6N-HRL-014",
    "mirror":        "PT-D6N-MIR-015"
}

VISION_PROMPT = """You are a CAT D6N dozer visual inspection AI.

CRITICAL RULE: Only describe what you can DIRECTLY SEE in this image.
Do NOT infer, assume, or describe components that are not clearly visible.
If you cannot clearly see a component, state that explicitly.
If image quality is poor, state that explicitly.

This is the #1 failure mode in inspection AI — describing the wrong
component or inventing findings not present in the image.

For each component you can ACTUALLY SEE, describe:
1. What component is visible (be specific to CAT D6N parts)
2. Its exact observed condition (use technical language)
3. Any anomalies: wear, damage, leaks, corrosion, missing hardware,
   deformation, cracks, or contamination
4. Your confidence that you are correctly identifying this component

Severity indicators:
- CRITICAL: visible structural failure, active leaks, missing hardware,
            cracks, severe corrosion — do not operate
- MODERATE: wear approaching limits, minor damage, maintenance needed
- LOW: surface wear, cosmetic issues, monitor at next service

Respond in JSON only. No markdown. No preamble. No backticks:
{
  "visible_components": ["list of components you can actually see"],
  "findings": [
    {
      "component": "exact part name",
      "observation": "precise description of what you see",
      "severity_indicator": "CRITICAL | MODERATE | LOW | NORMAL"
    }
  ],
  "confidence": integer 0-100,
  "image_quality": "clear | obstructed | insufficient_lighting"
}"""


DIGESTION_PROMPT_TEMPLATE = """You are a licensed CAT D6N dozer inspection AI generating a professional
inspection report that matches CAT Inspect documentation standards.

Technician voice note:
'{transcript}'

{vision_text}

Known D6N part numbers: {KNOWN_PARTS}

FUSION RULES:
- Voice and vision describe SAME component + SAME problem
    → set evidence_backed: true
- Voice and vision describe SAME component but DIFFERENT findings
    → set technician_review_required: true
- Voice only, no vision data
    → process transcript, set evidence_backed: false

SEVERITY RULES (use CAT's exact language):
- 'Critical'  = immediate shutdown, do not operate
- 'Moderate'  = schedule within 24-48 hours
- 'Low'       = monitor at next routine service

STATUS RULES (top-level):
- Any Critical anomaly present → status: 'fail'
- Only Moderate anomalies → status: 'monitor'
- Only Low or no anomalies → status: 'pass'

TIMELINE RULES:
- Critical: 'Replace immediately before next operation'
- Moderate: 'Address within 50 operating hours or 2 weeks'
- Low: 'Monitor and replace at next scheduled service'
Never use vague language like 'address soon' or 'check later.'

OUTPUT RULES:
- Respond in JSON only
- No markdown, no backticks, no preamble, no extra fields
- Match the anomalies array schema exactly
- Each anomaly gets its own object in the array
- If multiple issues found, list ALL of them

TARGET SCHEMA TO MATCH EXACTLY:
{
  "inspection_summary": {
    "asset": "CAT D6N Dozer",
    "status": "pass | monitor | fail",
    "overall_operational_impact": "string"
  },
  "anomalies": [
    {
      "component": "string — exact D6N part name",
      "component_location": "string — where on the machine",
      "issue": "string — short issue title",
      "condition_description": "string — precise technical description of what was observed",
      "severity": "Critical" | "Moderate" | "Low",
      "safety_impact_assessment": "string — personnel/operator risk",
      "operational_impact": "string — effect on machine function",
      "estimated_timeline": "string — specific e.g. 'Replace within 50 operating hours'",
      "recommended_action": "string — one clear technician instruction",
      "part_number": "string — from D6N lookup or null",
      "evidence_backed": boolean,
      "technician_review_required": boolean,
      "confidence_score": integer 0-100
    }
  ]
}"""


# ---------------------------------------------------------------------------
# FINE-TUNED ADAPTER CLASSIFIER
# Loads the LoRA adapter trained by pipeline.py from the shared Modal Volume.
# Returns a severity pre-classification (ASAP / Soon / Okay) from the
# fine-tuned Mistral-7B model. This is injected into Claude's prompt as a
# domain-grounded signal, improving severity accuracy for CAT D6N findings.
# ---------------------------------------------------------------------------
@app.function(
    image=adapter_image,
    gpu="A10G",
    timeout=120,
    volumes={"/data": adapter_volume},
)
def classify_with_adapter(transcript: str) -> dict:
    import os
    import gc
    import torch
    import json
    import re
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    # Prevent VRAM fragmentation between sequential calls
    os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

    # Check if a production adapter actually exists yet
    if not os.path.exists(ADAPTER_PROD):
        return {"severity": None, "rationale": None, "source": "no_adapter"}

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        cache_dir=MODEL_CACHE_DIR,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, cache_dir=MODEL_CACHE_DIR)
    model = PeftModel.from_pretrained(base, ADAPTER_PROD)
    model.eval()

    prompt = (
        "You are a CAT-certified D6N Track-Type Dozer technician and field inspector. "
        "You have memorized the D6N service manuals, parts reference guide, and fluid specifications.\n\n"
        "Given a field observation about the machine and a relevant excerpt from the service "
        "documentation, analyze the issue and output a structured JSON inspection finding with a "
        "severity rating of ASAP, Soon, or Okay.\n\n"
        f"OBSERVATION: {transcript}\n\nOutput JSON:"
    )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    # Free VRAM aggressively before returning — prevents OOM on next invocation
    del inputs, outputs, model, base
    gc.collect()
    torch.cuda.empty_cache()

    # Parse the severity from the model output
    try:
        clean = generated.strip()
        if clean.count("{") > clean.count("}"):
            clean += "}" * (clean.count("{") - clean.count("}"))
        pred = json.loads(clean)
        return {
            "severity": pred.get("severity"),
            "rationale": pred.get("rationale"),
            "recommended_action": pred.get("recommended_action"),
            "component": pred.get("component"),
            "source": "finetuned_adapter",
        }
    except Exception:
        # Regex fallback if JSON is still malformed
        sev = re.search(r'"severity"\s*:\s*"(ASAP|Soon|Okay)"', generated)
        return {
            "severity": sev.group(1) if sev else None,
            "rationale": None,
            "source": "finetuned_adapter_partial",
        }


@app.function(image=image, gpu="T4", timeout=60)
def transcribe_audio(audio_bytes: bytes) -> str:
    import whisper
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_filename = tmp_file.name
        
    try:
        model = whisper.load_model("small")  # 'small' >> 'base' for technical vocabulary
        result = model.transcribe(tmp_filename)
        return result["text"].strip()
    finally:
        if os.path.exists(tmp_filename):
            os.remove(tmp_filename)

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=60)
def analyze_image(image_bytes: bytes) -> dict | None:
    if not image_bytes:
        return None
        
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY secret not found.")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    data = {
        "model": "claude-sonnet-4-5",
        "max_tokens": 1024,
        "system": VISION_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64_image
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this inspection image and strictly follow the output format."
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            content_text = result["content"][0]["text"].strip()
            
            if content_text.startswith("```json"):
                content_text = content_text[7:]
            if content_text.startswith("```"):
                content_text = content_text[3:]
            if content_text.endswith("```"):
                content_text = content_text[:-3]
                
            return json.loads(content_text.strip())
            
    except Exception as e:
        print(f"Error in analyze_image: {e}")
        return None

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=60)
def extract_structured_note(transcript: str, vision_data: dict | None, adapter_classification: dict | None = None) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY secret not found.")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    vision_text = ""
    if vision_data:
        v_components = vision_data.get('visible_components', [])
        v_findings = vision_data.get('findings', [])
        v_quality = vision_data.get('image_quality', 'unknown')
        v_conf = vision_data.get('confidence', 0)
        
        vision_text = f'''Visual inspection confirmed:
  Components seen: {v_components}
  Visual findings: {v_findings}
  Image quality: {v_quality}
  Vision confidence: {v_conf}%'''
    else:
        vision_text = "No vision data available."

    # Inject fine-tuned adapter classification as a grounding signal
    adapter_text = ""
    if adapter_classification and adapter_classification.get("severity"):
        # Map ASAP/Soon/Okay → Critical/Moderate/Low to match CAT Inspect schema
        sev_map = {"ASAP": "Critical", "Soon": "Moderate", "Okay": "Low"}
        mapped_sev = sev_map.get(adapter_classification["severity"], adapter_classification["severity"])
        adapter_text = (
            f"\n\nFINE-TUNED MODEL PRE-CLASSIFICATION (CAT D6N domain expert signal):\n"
            f"  Severity: {mapped_sev}\n"
            f"  Component: {adapter_classification.get('component', 'Unknown')}\n"
            f"  Rationale: {adapter_classification.get('rationale', 'N/A')}\n"
            f"  Source: {adapter_classification.get('source', 'unknown')}\n"
            f"Use this as a strong prior — override only if voice/vision evidence clearly contradicts it."
        )

    prompt = DIGESTION_PROMPT_TEMPLATE.replace("{transcript}", transcript)
    prompt = prompt.replace("{vision_text}", vision_text + adapter_text)
    prompt = prompt.replace("{KNOWN_PARTS}", json.dumps(D6N_PARTS))

    data = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 2048,
        "system": "You respond in valid JSON only.",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            content_text = result["content"][0]["text"].strip()
            
            if content_text.startswith("```json"):
                content_text = content_text[7:]
            if content_text.startswith("```"):
                content_text = content_text[3:]
            if content_text.endswith("```"):
                content_text = content_text[:-3]
                
            return json.loads(content_text.strip())
            
    except Exception as e:
        print(f"Error in extract_structured_note: {e}")
        return {"error": "Failed to extract structured note", "details": str(e)}

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=120)
def digest_maintenance_event(audio_bytes: bytes, image_bytes: bytes | None = None):
    # Spawn EARS (Whisper), EYES (Claude Vision), and BRAIN (fine-tuned adapter) in parallel
    ears_call = transcribe_audio.spawn(audio_bytes)

    eyes_call = None
    if image_bytes is not None and len(image_bytes) > 0:
        eyes_call = analyze_image.spawn(image_bytes)

    # Wait for transcript first (needed to spawn adapter classifier)
    transcript = ears_call.get()

    # Now spawn the fine-tuned adapter classifier with the transcript
    adapter_call = classify_with_adapter.spawn(transcript)

    # Collect vision and adapter results
    vision_raw = None
    if eyes_call:
        vision_raw = eyes_call.get()

    adapter_classification = adapter_call.get()
    print(f"Adapter classification: {adapter_classification}")

    # Fuse everything into final structured report via Claude
    final_output = extract_structured_note.remote(transcript, vision_raw, adapter_classification)

    # Attach raw signals for transparency
    final_output["raw_transcript"] = transcript
    final_output["vision_raw"] = vision_raw
    final_output["adapter_classification"] = adapter_classification

    return final_output

@app.local_entrypoint()
def main(audio_path: str | None = None, image_path: str | None = None):
    # The requirement specifically mentions:
    # Exit gate command: modal run modal_app.py
    # so we need a default execution path when no arguments are provided.
    
    import sys
    
    if not audio_path:
        # Fallback to look for sample.wav if no arg provided
        if os.path.exists("sample.mp3"):
            audio_path = "sample.mp3"
        elif os.path.exists("sample.wav"):
            audio_path = "sample.wav"
        else:
            print("Usage: modal run modal_app.py --audio-path <audio_file> [--image-path <image_file>]")
            print("Or ensure 'sample.mp3' or 'sample.wav' exists in the current directory.")
            return

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
        
    image_bytes = None
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
    elif not image_path and os.path.exists("sample.jpg"):
        with open("sample.jpg", "rb") as f:
            image_bytes = f.read()

    print("Submitting digest_maintenance_event task to Modal...")
    result = digest_maintenance_event.remote(audio_bytes, image_bytes)
    print("\n--- FINAL JSON RESULT ---")
    print(json.dumps(result, indent=2))


@app.local_entrypoint()
def batch(audio_dir: str = "./audiotestcases", output: str = "./audiotestcases_results.json"):
    """
    Process all MP3s in audio_dir through the full pipeline.
    Usage: modal run modal_app.py::batch
           modal run modal_app.py::batch --audio-dir ./audiotestcases
    """
    mp3_files = sorted([
        f for f in os.listdir(audio_dir)
        if f.lower().endswith(".mp3")
    ])
    print(f"Found {len(mp3_files)} audio files in {audio_dir}\n")

    results = []
    for i, filename in enumerate(mp3_files):
        filepath = os.path.join(audio_dir, filename)
        print(f"[{i+1}/{len(mp3_files)}] {filename}")
        with open(filepath, "rb") as f:
            audio_bytes = f.read()
        try:
            result = digest_maintenance_event.remote(audio_bytes, None)
            result["_file"] = filename
            result["_index"] = i + 1
            results.append(result)

            summary     = result.get("inspection_summary", {})
            status      = summary.get("status", "?").upper()
            adapter_sev = (result.get("adapter_classification") or {}).get("severity", "N/A")
            anomalies   = len(result.get("anomalies", []))
            transcript  = result.get("raw_transcript", "")[:75]
            print(f"  Status: {status:<8} Adapter: {adapter_sev:<5} Anomalies: {anomalies}  \"{transcript}\"")
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({"_file": filename, "_index": i + 1, "error": str(e)})

    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Complete. {len(results)} results → {output}")
    print(f"{'='*60}\n")

    # Summary table
    pass_count    = sum(1 for r in results if r.get("inspection_summary", {}).get("status") == "pass")
    monitor_count = sum(1 for r in results if r.get("inspection_summary", {}).get("status") == "monitor")
    fail_count    = sum(1 for r in results if r.get("inspection_summary", {}).get("status") == "fail")
    error_count   = sum(1 for r in results if "error" in r)
    print(f"PASS: {pass_count}  MONITOR: {monitor_count}  FAIL: {fail_count}  ERROR: {error_count}")

