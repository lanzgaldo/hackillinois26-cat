"""
modal_app/worker.py
────────────────────
Modal AI deployment: GPU-accelerated inference worker.

Responsibilities:
  1. Receive image + metadata from the API endpoint or Antigravity pipeline
  2. Store/retrieve images from Modal Volume (persistent between calls)
  3. Call ContextBuilder to assemble the full context package
  4. Send context to Anthropic Claude vision API
  5. Validate output through SchemaValidator
  6. Write final JSON to Modal Volume output bucket
  7. Return structured result to caller

Deploy:
  modal deploy modal_app/worker.py

Invoke remotely:
  modal run modal_app/worker.py::inspect_image \
    --image-path /path/to/image.jpg \
    --category tires_rims \
    --profile default
"""

import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import modal

from context_engine.context_builder import ContextBuilder
from context_engine.schema_validator import SchemaValidator, ValidationResult
from context_engine.subsection_router import AutoDetectRequired
from context_engine.weight_calculator import WeightCalculator


# ─────────────────────────────────────────────────────────────────────────────
# MODAL APP + IMAGE DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

app = modal.App("cat-equipment-inspector")

# Dependencies bundled into the Modal container image
modal_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic>=0.25.0",
        "pydantic>=2.0",
        "pillow>=10.0",
    )
    .add_local_dir("context_engine", remote_path="/root/context_engine")
    .add_local_dir("schemas",        remote_path="/root/schemas")
    .add_local_dir("prompts",        remote_path="/root/prompts")
)

# Persistent volumes
input_volume  = modal.Volume.from_name("cat-inspector-inputs",  create_if_missing=True)
output_volume = modal.Volume.from_name("cat-inspector-outputs", create_if_missing=True)
prompt_volume = modal.Volume.from_name("cat-inspector-prompts", create_if_missing=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────────────────────────────────────
# Create in Modal dashboard: modal secret create anthropic-key ANTHROPIC_API_KEY=sk-...
anthropic_secret = modal.Secret.from_name("anthropic-key")


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DETECT CLASSIFIER (lightweight pre-pass)
# ─────────────────────────────────────────────────────────────────────────────

@app.function(
    image=modal_image,
    secrets=[anthropic_secret],
    volumes={"/inputs": input_volume},
    timeout=60,
)
def classify_component(image_bytes: bytes) -> str:
    """
    Lightweight single-call classifier that determines component_category
    from the image before the full inspection is run.

    Used when category='auto' is passed to inspect_image.

    Returns one of the SubsectionRouter.ROUTES keys.
    """
    import anthropic
    import base64

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    b64 = base64.b64encode(image_bytes).decode()

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",   # Fast, cheap classifier pass
        max_tokens=50,
        system=(
            "You are a CAT equipment component classifier. "
            "Look at the image and respond with ONLY one of these exact strings: "
            "tires_rims | steps_access | cooling | hydraulics | structural | engine | undercarriage. "
            "Nothing else."
        ),
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text",  "text": "What CAT equipment component is shown?"},
            ],
        }],
    )
    category = response.content[0].text.strip().lower()
    VALID = {"tires_rims", "steps_access", "cooling", "hydraulics", "structural", "engine", "undercarriage"}
    return category if category in VALID else "engine"


# ─────────────────────────────────────────────────────────────────────────────
# MAIN INSPECTION WORKER
# ─────────────────────────────────────────────────────────────────────────────

@app.function(
    image=modal_image,
    secrets=[anthropic_secret],
    volumes={
        "/inputs":  input_volume,
        "/outputs": output_volume,
        "/prompts": prompt_volume,
    },
    timeout=120,
    retries=modal.Retries(max_retries=2, backoff_coefficient=2.0, initial_delay=1.0),
)
def inspect_image(
    image_path:          str,
    component_category:  str = "auto",
    weight_profile:      str = "default",
    image_bytes:         bytes | None = None,
) -> dict:
    """
    Core inspection worker.

    Args:
        image_path:         Path to image (on Modal volume or local for testing)
        component_category: Category key or "auto" for classifier-assisted routing
        weight_profile:     Named weight profile from WeightCalculator
        image_bytes:        Raw image bytes (overrides disk read if provided)

    Returns:
        dict with keys: success, output_json, validation_corrections, run_metadata
    """
    import anthropic

    run_start = datetime.now(timezone.utc)
    client    = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # ── 1. Auto-detect category if needed ─────────────────────────────────────
    if component_category == "auto":
        raw_bytes = image_bytes or Path(image_path).read_bytes()
        component_category = classify_component.remote(raw_bytes)
        print(f"[worker] Auto-detected category: {component_category}")

    # ── 2. Build context package ───────────────────────────────────────────────
    builder = ContextBuilder()
    package = builder.build(
        image_path=image_path,
        component_category=component_category,
        weight_profile=weight_profile,
        image_bytes=image_bytes,
    )
    print(f"[worker] Context built: {component_category} | profile={weight_profile}")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    print(f"[worker] ANTHROPIC_API_KEY length: {len(api_key)}, starts with: {api_key[:5] if api_key else 'None'}")

    # ── 3. Call Anthropic ──────────────────────────────────────────────────────
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=package.system_prompt,
        messages=package.to_anthropic_messages(),
    )
    raw_text = response.content[0].text
    print(f"[worker] Model response received ({len(raw_text)} chars)")

    # ── 4. Validate + auto-correct ─────────────────────────────────────────────
    validator = SchemaValidator()
    result: ValidationResult = validator.validate(raw_text, package.weight_vector)

    run_meta = {
        "image_path":         image_path,
        "component_category": component_category,
        "weight_profile":     weight_profile,
        "subsection_file":    package.metadata.get("subsection_file"),
        "run_start":          run_start.isoformat(),
        "run_end":            datetime.now(timezone.utc).isoformat(),
        "validation_success": result.success,
        "corrections":        result.corrections,
        "errors":             result.errors,
    }

    if not result.success:
        print(f"[worker] Validation FAILED: {result.errors}")
        return {
            "success":    False,
            "output_json": None,
            "raw_output":  raw_text,
            "run_metadata": run_meta,
        }

    # ── 5. Write to output volume ──────────────────────────────────────────────
    output_json = result.output.model_dump()
    output_path = Path(f"/outputs/{Path(image_path).stem}_{run_start.strftime('%Y%m%dT%H%M%S')}.json")
    output_path.write_text(json.dumps(output_json, indent=2))
    output_volume.commit()
    print(f"[worker] Output written: {output_path}")

    return {
        "success":               True,
        "output_json":           output_json,
        "output_path":           str(output_path),
        "validation_corrections": result.corrections,
        "run_metadata":          run_meta,
    }


# ─────────────────────────────────────────────────────────────────────────────
# BATCH WORKER — process multiple images in parallel
# ─────────────────────────────────────────────────────────────────────────────

@app.function(
    image=modal_image,
    secrets=[anthropic_secret],
    volumes={"/inputs": input_volume, "/outputs": output_volume},
    timeout=600,
)
def batch_inspect(jobs: list[dict]) -> list[dict]:
    """
    Runs inspect_image.remote() for each job in parallel using Modal's
    built-in .map() / starmap().

    Args:
        jobs: List of dicts, each with keys:
                image_path, component_category, weight_profile

    Returns:
        List of result dicts in same order as input
    """
    results = list(
        inspect_image.starmap(
            [
                (
                    j["image_path"],
                    j.get("component_category", "auto"),
                    j.get("weight_profile", "default"),
                )
                for j in jobs
            ]
        )
    )
    return results


# ─────────────────────────────────────────────────────────────────────────────
# LOCAL ENTRYPOINT (for CLI testing without full Modal deploy)
# ─────────────────────────────────────────────────────────────────────────────

@app.local_entrypoint()
def main(
    image_path:         str = "tests/fixtures/BrokenRimBolt1.jpg",
    category:           str = "tires_rims",
    weight_profile:     str = "default",
):
    result = inspect_image.remote(
        image_path=image_path,
        component_category=category,
        weight_profile=weight_profile,
    )
    print(json.dumps(result, indent=2))
