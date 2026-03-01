"""
catrack_provider.py — FastAPI Gateway + Adapter Classifier for lanzgaldo
────────────────────────────────────────────────────────────────────────
Deployed on lanzgaldo as: catrack-provider

This app serves two purposes:
  1. FastAPI gateway that proxies /extract, /synthesize, /transcribe to
     cleanpxe web endpoints over HTTPS.
  2. Hosts the fine-tuned Mistral-7B LoRA adapter classifier, since the
     trained weights live on lanzgaldo's d6n-training-vault volume.

Deploy:
    modal deploy catrack_provider.py   (run under lanzgaldo credentials)

The cleanpxe backend must also be deployed:
    modal deploy modal_app.py          (run under cleanpxe credentials)
"""

import os
import json
import modal

app = modal.App("catrack-provider")

gateway_image = modal.Image.debian_slim().pip_install("requests", "fastapi[standard]")

# ── Adapter infrastructure (Mistral-7B with LoRA) ──
adapter_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(["torch", "transformers", "peft", "accelerate", "bitsandbytes", "fastapi[standard]"])
)
adapter_volume = modal.Volume.from_name("d6n-training-vault", create_if_missing=True)
ADAPTER_PROD    = "/data/adapters/production/v1"
BASE_MODEL      = "mistralai/Mistral-7B-Instruct-v0.2"
MODEL_CACHE_DIR = "/data/models/mistral-7b"


# ─────────────────────────────────────────────────────────────────────────────
# CLEANPXE BACKEND URLS
# ─────────────────────────────────────────────────────────────────────────────
CLEANPXE_BASE = "https://cleanpxe--cat-inspect-ai-sprint1"
BACKEND = {
    "health":     f"{CLEANPXE_BASE}-web-health.modal.run",
    "transcribe": f"{CLEANPXE_BASE}-web-transcribe.modal.run",
    "vision":     f"{CLEANPXE_BASE}-web-analyze-image.modal.run",
    "extract":    f"{CLEANPXE_BASE}-web-extract.modal.run",
    "synthesize": f"{CLEANPXE_BASE}-web-synthesize.modal.run",
}


# ─────────────────────────────────────────────────────────────────────────────
# FINE-TUNED ADAPTER CLASSIFIER (runs on lanzgaldo GPU with trained weights)
# ─────────────────────────────────────────────────────────────────────────────

@app.function(
    image=adapter_image,
    gpu="A10G",
    timeout=120,
    volumes={"/data": adapter_volume},
)
def classify_with_adapter(transcript: str) -> dict:
    import os, gc, torch, json, re
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel

    os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

    if not os.path.exists(ADAPTER_PROD):
        return {"severity": None, "rationale": None, "source": "no_adapter"}

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, quantization_config=bnb_config,
        device_map="auto", cache_dir=MODEL_CACHE_DIR,
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
            **inputs, max_new_tokens=256, do_sample=False,
            temperature=1.0, pad_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    del inputs, outputs, model, base
    gc.collect()
    torch.cuda.empty_cache()

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
        sev = re.search(r'"severity"\s*:\s*"(ASAP|Soon|Okay)"', generated)
        return {
            "severity": sev.group(1) if sev else None,
            "rationale": None,
            "source": "finetuned_adapter_partial",
        }


@app.function(image=adapter_image, gpu="A10G", timeout=120, volumes={"/data": adapter_volume})
@modal.fastapi_endpoint(method="POST")
def web_classify(item: dict):
    """HTTPS endpoint: Run the fine-tuned adapter classifier.
    Expects {"transcript": "..."}
    Returns {"severity": "ASAP|Soon|Okay", "rationale": "...", "source": "finetuned_adapter"}
    """
    transcript = item.get("transcript", "")
    if not transcript:
        return {"severity": None, "rationale": None, "source": "no_transcript"}
    return classify_with_adapter.remote(transcript)


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI GATEWAY (proxies to cleanpxe over HTTPS)
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

web_app = FastAPI(
    title="CATrack Inspection AI",
    description=(
        "Human-in-the-Loop inspection pipeline for CAT D6N heavy equipment.\n"
        "Stage 1: /extract  |  Stage 3: /synthesize\n\n"
        "Gateway on lanzgaldo. Vision+JSON on cleanpxe. "
        "Adapter classifier (Mistral-7B) on lanzgaldo."
    ),
    version="2.1.0",
)


class ExtractRequest(BaseModel):
    """Stage 1 input."""
    audio_b64: str
    image_b64: Optional[str] = None
    job_id: Optional[str] = None
    category: str = "auto"


class SynthesizeRequest(BaseModel):
    """Stage 3 input — verified JSON after human review."""
    verified_json: dict
    job_id: Optional[str] = None


class TranscribeRequest(BaseModel):
    audio_b64: str


def _call_backend(endpoint_key: str, payload: dict, timeout: int = 180) -> dict:
    """Call a cleanpxe web endpoint over HTTPS."""
    import requests as req
    url = BACKEND[endpoint_key]
    try:
        resp = req.post(url, json=payload, timeout=timeout)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Backend ({endpoint_key}) error: {resp.text[:500]}"
            )
        return resp.json()
    except req.exceptions.Timeout:
        raise HTTPException(504, f"Backend ({endpoint_key}) timed out after {timeout}s")
    except req.exceptions.ConnectionError as e:
        raise HTTPException(502, f"Backend ({endpoint_key}) unreachable: {str(e)[:200]}")


@web_app.get("/health")
def health():
    import requests as req
    backend_status = "unknown"
    try:
        r = req.get(BACKEND["health"], timeout=5)
        backend_status = r.json() if r.status_code == 200 else f"error:{r.status_code}"
    except Exception as e:
        backend_status = f"unreachable: {str(e)[:100]}"

    adapter_exists = os.path.exists(ADAPTER_PROD) if os.path.exists("/data") else "volume_not_mounted"

    return {
        "status": "ok",
        "version": "2.1.0",
        "gateway": "lanzgaldo",
        "adapter_available": adapter_exists,
        "backend": backend_status,
        "endpoints": ["/extract", "/synthesize", "/transcribe", "/classify", "/health"],
    }


@web_app.post("/extract")
def extract(req: ExtractRequest):
    """STAGE 1 — Full AI extraction. Bridges to cleanpxe for vision+JSON."""
    payload = {"audio_b64": req.audio_b64, "category": req.category}
    if req.image_b64:
        payload["image_b64"] = req.image_b64
    result = _call_backend("extract", payload, timeout=180)
    if req.job_id:
        result["job_id"] = req.job_id
    return result


@web_app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    """STAGE 3 — Professional report generation after human review."""
    result = _call_backend("synthesize", {"verified_json": req.verified_json}, timeout=60)
    if req.job_id:
        result["job_id"] = req.job_id
    return result


@web_app.post("/transcribe")
def transcribe(req: TranscribeRequest):
    """Audio-only transcription via Whisper on cleanpxe."""
    return _call_backend("transcribe", {"audio_b64": req.audio_b64}, timeout=60)


@web_app.post("/classify")
def classify_endpoint(item: dict):
    """Run the fine-tuned Mistral-7B adapter classifier on lanzgaldo.
    Expects {"transcript": "..."}
    """
    transcript = item.get("transcript", "")
    if not transcript:
        return {"severity": None, "rationale": None, "source": "no_transcript"}
    return classify_with_adapter.remote(transcript)


@app.function(image=gateway_image, timeout=300)
@modal.asgi_app()
def fastapi_app():
    return web_app
