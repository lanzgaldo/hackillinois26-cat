"""
CATrack Inspection AI — Teammate Client
pip install requests  (that's the only dependency)

Usage:
    from integration_client import run_inspection, pretty_print

    result = run_inspection("field_note.mp3")
    pretty_print(result)

    # Full pipeline with image:
    result = run_inspection("field_note.mp3", image_path="photo.jpg")
    pretty_print(result)

    # Stage 3 — after human review/edit in Expo UI:
    from integration_client import synthesize_report
    report = synthesize_report(result)
    print(report["report"])
"""

import base64
import json
import requests

API_URL = "https://lanzgaldo--catrack-provider-fastapi-app.modal.run"


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def health_check() -> dict:
    """Check the API is alive."""
    return requests.get(f"{API_URL}/health", timeout=10).json()


def run_inspection(audio_path: str, image_path: str | None = None,
                   job_id: str | None = None, timeout: int = 180) -> dict:
    """
    STAGE 1 — Full CAT D6N AI extraction from a voice note + optional photo.
    Runs Whisper, fine-tuned LoRA adapter, Claude vision, and structured note
    extraction in parallel on Modal.

    Returns proposed inspection JSON with:
      inspection_summary  -> { status: pass/monitor/fail, ... }
      anomalies[]         -> severity, recommended_action, part_number, ...
      raw_transcript      -> what Whisper heard
      adapter_classification -> fine-tuned model severity signal

    This output is meant for human review in the Expo UI before Stage 3.
    """
    payload = {"audio_b64": _b64(audio_path)}
    if image_path:
        payload["image_b64"] = _b64(image_path)
    if job_id:
        payload["job_id"] = job_id

    resp = requests.post(f"{API_URL}/extract", json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def synthesize_report(verified_json: dict, job_id: str | None = None,
                      timeout: int = 60) -> dict:
    """
    STAGE 3 — Professional report generation.
    Call this ONLY after the human has reviewed/edited the Stage 1 output
    in the Expo UI.

    Takes the verified JSON dict and returns a professional paragraph-style
    inspection report in Construction Inspector tone.
    """
    payload = {"verified_json": verified_json}
    if job_id:
        payload["job_id"] = job_id

    resp = requests.post(f"{API_URL}/synthesize", json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def transcribe_audio(audio_path: str, timeout: int = 60) -> str:
    """Transcribe a field voice note. Returns plain text string."""
    resp = requests.post(f"{API_URL}/transcribe",
                         json={"audio_b64": _b64(audio_path)}, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("transcript", "")


def pretty_print(result: dict) -> None:
    """Print a human-readable summary to the terminal."""
    s = result.get("inspection_summary", {})
    status = s.get("status", "?").upper()
    icon = {"PASS": "[PASS]", "MONITOR": "[MONITOR]", "FAIL": "[FAIL]"}.get(status, "[?]")
    print(f"\n{'='*55}")
    print(f"  {icon} {status}  --  {s.get('asset', 'CAT D6N Dozer')}")
    print(f"  {s.get('overall_operational_impact', '')}")
    transcript = result.get("raw_transcript", "")
    if transcript:
        print(f'  Heard: "{transcript}"')
    anomalies = result.get("anomalies", [])
    if anomalies:
        print(f"\n  Anomalies ({len(anomalies)}):")
        for a in anomalies:
            sev = a.get("severity", "?")
            tag = {"Critical": "[CRIT]", "Moderate": "[MOD]", "Low": "[LOW]"}.get(sev, "[?]")
            print(f"    {tag} {a.get('component', '?')} -- {a.get('recommended_action', 'N/A')}")
    else:
        print("  No anomalies.")
    print(f"{'='*55}\n")


# CLI: python integration_client.py audio.mp3 [photo.jpg]
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python integration_client.py <audio.mp3> [photo.jpg]")
        sys.exit(1)
    result = run_inspection(sys.argv[1],
                            image_path=sys.argv[2] if len(sys.argv) > 2 else None)
    pretty_print(result)
    out = sys.argv[1].rsplit(".", 1)[0] + "_report.json"
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved -> {out}")
