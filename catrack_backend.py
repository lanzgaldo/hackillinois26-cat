"""
catrack_backend.py — CATrack AI-as-a-Service (Human-in-the-Loop Architecture)
===============================================================================
Three-stage HITL pipeline:

  Stage 1  POST /extract    Audio + image → proposed JSON for human review
  Stage 2  (Expo UI)        Human taps to verify/correct the proposed JSON
  Stage 3  POST /synthesize Verified JSON → professional Claude narrative

  Utility:
           GET  /health     Liveness check
           POST /transcribe Audio → plain text transcript only

Deploy:
    python -m modal deploy catrack_backend.py

Secrets required in Modal Dashboard → Secrets:
    Secret name: anthropic-secret
    Key: ANTHROPIC_API_KEY
"""

import base64
import json
import urllib.request
import modal

# ──────────────────────────────────────────────────────────────────────────────
# Infrastructure
# ──────────────────────────────────────────────────────────────────────────────

app = modal.App("catrack-provider")

volume = modal.Volume.from_name("d6n-training-vault", create_if_missing=False)

# Lightweight web layer — FastAPI only, no GPU
web_image = (
    modal.Image.debian_slim()
    .pip_install("fastapi", "pydantic", "anthropic")
)

# ──────────────────────────────────────────────────────────────────────────────
# Claude system prompt for Stage 3 synthesis
# Professional "Construction Inspector" tone for foreman reports
# ──────────────────────────────────────────────────────────────────────────────

SYNTHESIS_SYSTEM_PROMPT = """\
You are a licensed heavy equipment inspection report writer for a construction company.

Your job is to convert structured inspection data (provided as JSON) into a \
professional, plain-English inspection report suitable for a site foreman or \
fleet manager. The report should read like it was written by a senior field \
inspector — concise, factual, and professionally toned.

RULES:
- Write in clear paragraph form. No bullet points, no headers, no markdown.
- Use precise technical language for components (e.g. "final drive assembly", \
"duo-cone seal", "hydraulic charge circuit").
- State the severity and recommended action explicitly.
- If status is "fail", begin with a clear safety statement: \
"This machine must be removed from service immediately pending inspection."
- If status is "monitor", begin with: \
"This machine may remain in service with the following conditions noted."
- If status is "pass", begin with: \
"Inspection complete. No deficiencies requiring immediate action were identified."
- Close every report with: "Reported by CATrack AI Inspection System | \
Requires technician countersignature before filing."
- Respond with plain text only. No JSON. No lists.
"""


# ──────────────────────────────────────────────────────────────────────────────
# Modal web function
# ──────────────────────────────────────────────────────────────────────────────

@app.function(
    image=web_image,
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("anthropic-secret")],
)
@modal.asgi_app()
def fastapi_app():
    import os
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel

    # ── Request models ──────────────────────────────────────────────────────

    class ExtractRequest(BaseModel):
        """
        Stage 1 input.
        audio_b64   : base64-encoded MP3 or WAV. Required.
        image_b64   : base64-encoded JPEG or PNG. Optional.
        job_id      : optional tracking tag.
        """
        audio_b64: str
        image_b64: str | None = None
        job_id: str | None = None

    class SynthesizeRequest(BaseModel):
        """
        Stage 3 input — the JSON that came out of Stage 1 AFTER human review.
        verified_json: the full dict the human approved/edited in the Expo form.
        job_id       : optional tracking tag (echo it back in response).
        """
        verified_json: dict
        job_id: str | None = None

    class TranscribeRequest(BaseModel):
        audio_b64: str

    # ── FastAPI app ─────────────────────────────────────────────────────────

    web = FastAPI(
        title="CATrack Inspection AI",
        description=(
            "Human-in-the-Loop inspection pipeline for CAT D6N heavy equipment. "
            "Stage 1: /extract  |  Stage 3: /synthesize"
        ),
        version="2.0.0",
    )

    # ── Health ──────────────────────────────────────────────────────────────

    @web.get("/health")
    async def health():
        return {
            "status": "ok",
            "version": "2.0.0",
            "endpoints": ["/extract", "/synthesize", "/transcribe", "/health"],
        }

    # ── Stage 1: Extract ────────────────────────────────────────────────────

    @web.post("/extract")
    async def extract(req: ExtractRequest):
        """
        STAGE 1 — Raw AI extraction. Call this when the user finishes recording.

        Runs:
          • Whisper (small)  → transcript
          • Fine-tuned LoRA  → severity classification
          • Claude vision    → image findings (if image provided)
          • extract_structured_note → proposed structured JSON

        Returns the proposed JSON dict for the Expo UI to display for human review.
        The human can tap any field to correct it before hitting "Submit Final".
        """
        try:
            audio_bytes = base64.b64decode(req.audio_b64)
        except Exception:
            raise HTTPException(400, detail="audio_b64 is not valid base64.")

        image_bytes = None
        if req.image_b64:
            try:
                image_bytes = base64.b64decode(req.image_b64)
            except Exception:
                raise HTTPException(400, detail="image_b64 is not valid base64.")

        # Delegate to the existing sprint-1 pipeline functions
        digest = modal.Function.from_name(
            "cat-inspect-ai-sprint1", "digest_maintenance_event"
        )
        try:
            result = digest.remote(audio_bytes, image_bytes)
        except Exception as e:
            raise HTTPException(500, detail=f"Extraction failed: {str(e)}")

        if req.job_id:
            result["job_id"] = req.job_id

        # Tag this as a Stage 1 result so Expo knows it needs human review
        result["_stage"] = "proposed"
        result["_requires_verification"] = True

        return result

    # ── Stage 3: Synthesize ─────────────────────────────────────────────────

    @web.post("/synthesize")
    async def synthesize(req: SynthesizeRequest):
        """
        STAGE 3 — Professional report generation. Call this ONLY after the
        human has reviewed and approved/edited the Stage 1 output in the Expo UI.

        Takes the verified JSON dict and asks Claude to write a professional
        paragraph-style inspection report in Construction Inspector tone.

        The report is ready to hand to the foreman or file in the system.
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(500, detail="ANTHROPIC_API_KEY not configured.")

        # Build the prompt from the verified JSON
        verified = req.verified_json
        summary = verified.get("inspection_summary", {})
        anomalies = verified.get("anomalies", [])
        transcript = verified.get("raw_transcript", "")
        adapter = verified.get("adapter_classification", {})

        user_prompt = (
            f"Write a professional inspection report based on the following "
            f"verified inspection data.\n\n"
            f"INSPECTION SUMMARY:\n{json.dumps(summary, indent=2)}\n\n"
            f"ANOMALIES FOUND ({len(anomalies)}):\n{json.dumps(anomalies, indent=2)}\n\n"
            f"TECHNICIAN VOICE NOTE (verbatim): \"{transcript}\"\n\n"
            f"AI SEVERITY SIGNAL: {adapter.get('severity', 'N/A')} "
            f"({adapter.get('source', 'unknown')})\n\n"
            f"Write the report now:"
        )

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        data = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "system": SYNTHESIS_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        req_obj = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req_obj) as response:
                result = json.loads(response.read().decode("utf-8"))
                report_text = result["content"][0]["text"].strip()
        except Exception as e:
            raise HTTPException(500, detail=f"Claude synthesis failed: {str(e)}")

        # Save to volume as a persistent log (append mode)
        try:
            with open("/data/reports.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{'='*60}\n")
                if req.job_id:
                    f.write(f"JOB ID: {req.job_id}\n")
                f.write(report_text)
                f.write(f"\n{'='*60}\n")
        except Exception:
            pass  # Non-fatal — don't fail the response if volume write fails

        return {
            "report": report_text,
            "job_id": req.job_id,
            "verified_json": verified,
            "_stage": "final",
        }

    # ── Utility: Transcribe only ─────────────────────────────────────────────

    @web.post("/transcribe")
    async def transcribe(req: TranscribeRequest):
        """Audio-only transcription via Whisper. Returns plain text."""
        try:
            audio_bytes = base64.b64decode(req.audio_b64)
        except Exception:
            raise HTTPException(400, detail="audio_b64 is not valid base64.")

        fn = modal.Function.from_name("cat-inspect-ai-sprint1", "transcribe_audio")
        try:
            transcript = fn.remote(audio_bytes)
        except Exception as e:
            raise HTTPException(500, detail=f"Transcription failed: {str(e)}")

        return {"transcript": transcript}

    return web
