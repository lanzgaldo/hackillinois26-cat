import os
import json
import base64
import tempfile
import urllib.request
import urllib.error
import asyncio

import modal

app = modal.App("cat-inspect-ai-sprint1")
vol = modal.Volume.from_name("cat-inspector-outputs", create_if_missing=True)

# Shared volume where the fine-tuned LoRA adapter lives (written by pipeline.py)
# Volume resolves to the workspace where this app is deployed (lanzgaldo for prod)
adapter_volume = modal.Volume.from_name("d6n-training-vault", create_if_missing=True)
ADAPTER_PROD      = "/data/adapters/production/v1"
BASE_MODEL        = "mistralai/Mistral-7B-Instruct-v0.2"
MODEL_CACHE_DIR   = "/data/models/mistral-7b"

image = modal.Image.debian_slim().apt_install("ffmpeg").pip_install(
    "openai-whisper", "transformers", "torch", "pillow", "accelerate", "pydantic", "fastapi[standard]"
).add_local_dir("cat-inspector/schemas", remote_path="/root/schemas"
).add_local_dir("cat-inspector/pipeline", remote_path="/root/pipeline"
).add_local_dir("cat-inspector/context_engine", remote_path="/root/context_engine"
).add_local_dir("cat-inspector/prompts", remote_path="/root/prompts")

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

Here is the fully pre-computed Canonical Inspection Context from the AI Fusion Layer:
{canonical_context}

Known D6N part numbers: {KNOWN_PARTS}

FUSION RULES:
- The Context Bucket has already resolved overlapping components and conflicts.
- Format the final InspectionOutput matching the JSON schema EXACTLY.
- Do NOT alter severity ratings from the pre-computed contexts.
- Pass through the `is_global_safety_override`, `segment_mismatch_flag`, `global_override_category`, and `evidence_backed` properties.
- CRITICAL: If a finding in the context has `is_global_safety_override=True`, you MUST include it in the final anomalies array, even if the inferred severity is 'Normal'.

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
      "confidence_score": integer 0-100,
      "is_global_safety_override": boolean,
      "segment_mismatch_flag": boolean,
      "global_override_category": "string or null"
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
def analyze_image(image_bytes: bytes, category: str = "auto") -> dict | None:
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

    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from context_engine.subsection_router import SubsectionRouter
    
    router = SubsectionRouter()
    combined_prompt, resolved_category, _ = router.load_subsection_prompt(category)
    
    text_instruction = f"""ACTIVE INSPECTION SEGMENT: {resolved_category}
SEGMENT PRIORITY: Evaluate the image against the segment criteria below.

{combined_prompt}

RESPONSE INSTRUCTIONS:
Return a single JSON object.
Each finding MUST include is_global_safety_override: true/false.
Segment anomalies: is_global_safety_override = false
Global safety anomalies: is_global_safety_override = true

Do NOT omit global safety findings because they are off-segment.
Do NOT force-fit global safety components into segment vocabulary.

CRITICAL: 
- severity_indicator MUST be exactly one of: "CRITICAL", "MODERATE", "LOW", "NORMAL". Do NOT use "UNASSESSABLE".
- image_quality MUST be exactly one of: "clear", "obstructed", "insufficient_lighting". Do NOT use "low_for_segment".

Respond in JSON only. No markdown. No preamble. No backticks:
{{
  "visible_components": ["list of components you can actually see"],
  "findings": [
    {{
      "component": "exact part name",
      "observation": "precise description of what you see",
      "severity_indicator": "CRITICAL",
      "is_global_safety_override": true,
      "segment_mismatch_flag": true,
      "global_override_category": "access_egress"
    }}
  ],
  "confidence": 95,
  "image_quality": "clear"
}}"""

    data = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
        "system": "You are a CAT D6N dozer visual inspection AI. You strictly follow instructions and always return valid JSON without markdown wrapping.",
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
                        "text": text_instruction
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
        try:
            print(f"Raw text was:\n{content_text}")
        except:
            pass
        return None

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=60)
def extract_structured_note(canonical_context: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY secret not found.")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    prompt = DIGESTION_PROMPT_TEMPLATE.replace("{canonical_context}", canonical_context)
    prompt = prompt.replace("{KNOWN_PARTS}", json.dumps(D6N_PARTS))

    data = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
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
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTPError in extract_structured_note: {e.code} - {error_body}")
        return {"error": "Failed to extract structured note", "details": f"HTTP Error {e.code}: {error_body}"}
    except Exception as e:
        print(f"Error in extract_structured_note: {e}")
        return {"error": "Failed to extract structured note", "details": str(e)}

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], volumes={"/outputs": vol}, timeout=180)
def digest_maintenance_event(audio_bytes: bytes, image_bytes: bytes | None = None, component_category: str = "auto"):
    # Input validation
    if not audio_bytes:
        raise ValueError("Audio missing for inference.")
        
    ears_call = transcribe_audio.spawn(audio_bytes)

    eyes_call = None
    if image_bytes is not None and len(image_bytes) > 0:
        eyes_call = analyze_image.spawn(image_bytes, component_category)
        
    transcript = ears_call.get()
    
    # ── Call lanzgaldo's fine-tuned adapter via HTTPS ──
    # The trained Mistral-7B weights live on lanzgaldo's d6n-training-vault
    LANZGALDO_CLASSIFY_URL = "https://lanzgaldo--catrack-provider-web-classify.modal.run"
    adapter_classification = {"severity": None, "rationale": None, "source": "no_adapter"}
    if transcript and transcript.strip():
        try:
            import urllib.request
            classify_payload = json.dumps({"transcript": transcript}).encode("utf-8")
            classify_req = urllib.request.Request(
                LANZGALDO_CLASSIFY_URL,
                data=classify_payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(classify_req, timeout=90) as resp:
                adapter_classification = json.loads(resp.read().decode("utf-8"))
            print(f"Adapter classification from lanzgaldo: {adapter_classification}")
        except Exception as e:
            print(f"Adapter call to lanzgaldo failed (non-fatal): {e}")
            adapter_classification = {"severity": None, "rationale": None, "source": "bridge_error"}
    
    vision_raw = None
    if eyes_call:
        vision_raw = eyes_call.get()
        
    import asyncio
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from pipeline.context_bucket import build_context_bucket, write_context_json
    
    context = asyncio.run(build_context_bucket(
        raw_transcript=transcript,
        raw_vision=vision_raw,
        raw_adapter=adapter_classification,
        adapter_version="v1",
        component_category=component_category,
        inspection_type="daily_walkaround"
    ))
    
    context_path = write_context_json(context, output_dir="/outputs")
    final_output = extract_structured_note.remote(context.model_dump_json())
    
    return {
        "context_path": context_path,
        "inspection_output": final_output
    }

@app.local_entrypoint()
def main(audio_path: str | None = None, image_path: str | None = None, category: str = "auto"):
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

    print(f"Submitting digest_maintenance_event task to Modal for category '{category}'...")
    result = digest_maintenance_event.remote(audio_bytes, image_bytes, category)
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


# ─────────────────────────────────────────────────────────────────────────────
# HTTPS WEB ENDPOINTS — Exposed for cross-workspace bridge from lanzgaldo
# These run on cleanpxe and are called by the catrack_provider gateway.
# ─────────────────────────────────────────────────────────────────────────────

@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=60)
@modal.fastapi_endpoint(method="POST")
def web_transcribe(item: dict):
    """HTTPS endpoint: transcribe audio. Expects {"audio_b64": "..."}"""
    import base64
    audio_b64 = item.get("audio_b64", "")
    if not audio_b64:
        return {"error": "audio_b64 is required"}
    audio_bytes = base64.b64decode(audio_b64)
    transcript = transcribe_audio.remote(audio_bytes)
    return {"transcript": transcript}


@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=120)
@modal.fastapi_endpoint(method="POST")
def web_analyze_image(item: dict):
    """HTTPS endpoint: Claude vision analysis. Expects {"image_b64": "...", "category": "auto"}"""
    import base64
    image_b64 = item.get("image_b64", "")
    category = item.get("category", "auto")
    if not image_b64:
        return {"error": "image_b64 is required"}
    image_bytes = base64.b64decode(image_b64)
    result = analyze_image.remote(image_bytes, category)
    return {"vision_result": result}


@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], volumes={"/outputs": vol}, timeout=180)
@modal.fastapi_endpoint(method="POST")
def web_extract(item: dict):
    """
    HTTPS endpoint: Full inspection pipeline.
    Expects {"audio_b64": "...", "image_b64": "...(optional)", "category": "auto"}
    Returns the same output as digest_maintenance_event.
    """
    import base64
    audio_b64 = item.get("audio_b64", "")
    image_b64 = item.get("image_b64")
    category = item.get("category", "auto")
    
    if not audio_b64:
        return {"error": "audio_b64 is required"}
    
    audio_bytes = base64.b64decode(audio_b64)
    image_bytes = base64.b64decode(image_b64) if image_b64 else None
    
    result = digest_maintenance_event.remote(audio_bytes, image_bytes, category)
    return result


@app.function(image=image, secrets=[modal.Secret.from_name("anthropic-secret")], timeout=60)
@modal.fastapi_endpoint(method="POST")
def web_synthesize(item: dict):
    """
    HTTPS endpoint: Stage 3 report synthesis.
    Expects {"verified_json": {...}}
    Calls extract_structured_note with the verified context.
    """
    verified = item.get("verified_json", {})
    if not verified:
        return {"error": "verified_json is required"}
    report = extract_structured_note.remote(json.dumps(verified))
    return {"report": report}


@app.function(image=image, timeout=10)
@modal.fastapi_endpoint(method="GET")
def web_health():
    """HTTPS health check for the cleanpxe backend."""
    return {
        "status": "ok",
        "workspace": "cleanpxe",
        "app": "cat-inspect-ai-sprint1",
        "endpoints": ["web_transcribe", "web_analyze_image", "web_extract", "web_synthesize"]
    }
