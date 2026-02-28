import os
import json
import base64
import tempfile
import urllib.request
import urllib.error
import asyncio

import modal

app = modal.App("cat-inspect-ai-sprint1")

image = modal.Image.debian_slim().apt_install("ffmpeg").pip_install(
    "openai-whisper", "transformers", "torch", "pillow", "accelerate"
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

@app.function(image=image, gpu="T4", timeout=60)
def transcribe_audio(audio_bytes: bytes) -> str:
    import whisper
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_filename = tmp_file.name
        
    try:
        model = whisper.load_model("base")
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
        "model": "claude-3-5-sonnet-20241022",
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
def extract_structured_note(transcript: str, vision_data: dict | None) -> dict:
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

    prompt = DIGESTION_PROMPT_TEMPLATE.replace("{transcript}", transcript)
    prompt = prompt.replace("{vision_text}", vision_text)
    prompt = prompt.replace("{KNOWN_PARTS}", json.dumps(D6N_PARTS))

    data = {
        "model": "claude-3-5-sonnet-20241022",
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
def digest_maintenance_event(audio_bytes: bytes, image_bytes: bytes = None):
    # This runs remotely as the orchestrator.
    # We fork EARS and EYES using Modal's .spawn() to execute them in parallel on separate remote workers
    
    ears_call = transcribe_audio.spawn(audio_bytes)
    
    eyes_call = None
    if image_bytes is not None and len(image_bytes) > 0:
        eyes_call = analyze_image.spawn(image_bytes)
    
    # Wait for results
    transcript = ears_call.get()
    
    vision_raw = None
    if eyes_call:
        vision_raw = eyes_call.get()
        
    # Run digestion sequentially after both are done
    final_output = extract_structured_note.local(transcript, vision_raw) 
    # Use .local() since we are already inside a remote function running digest_maintenance_event
    # Or, we can just call the extraction remotely using `.remote()`
    # Let's use remote call to encapsulate the resource logic cleanly
    final_output = extract_structured_note.remote(transcript, vision_raw)
    
    # Attach raw logs
    final_output["raw_transcript"] = transcript
    final_output["vision_raw"] = vision_raw
    
    return final_output

@app.local_entrypoint()
def main(audio_path: str = None, image_path: str = None):
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
