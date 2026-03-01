import json
import os
from datetime import datetime, timezone
from typing import Optional, Literal
from schemas.context_schema import CanonicalInspectionContext
from pipeline.perceptor_normalizer import normalize_voice, normalize_vision, normalize_adapter
from pipeline.fusion_engine import run_fusion, _derive_preliminary_status, _generate_ai_overview

async def build_context_bucket(
    raw_transcript: Optional[str] = None,
    raw_vision: Optional[dict] = None,
    raw_adapter: Optional[dict] = None,
    adapter_version: Optional[str] = None,
    component_category: str = "auto",
    inspection_type: Literal["daily_walkaround", "safety", "TA1", "custom"] = "daily_walkaround",
    session_id: Optional[str] = None,
    image_filename: Optional[str] = None
) -> CanonicalInspectionContext:
    """
    Orchestrates the full context bucket pipeline.
    Single entry point that downstream callers use.
    Never raises. Degrades gracefully on missing inputs.
    """
    # ── 1. Normalize Perceptor Outputs ──
    v_context = None
    vi_context = None
    missing = []
    
    try:
        v_context = normalize_voice(raw_transcript)
        if not v_context:
            missing.append("voice_input")
    except Exception as e:
        print(f"[context_bucket] Voice normalization failed: {e}")
        missing.append("voice_input")

    try:
        vi_context = normalize_vision(raw_vision)
        if not vi_context:
            missing.append("image_input")
    except Exception as e:
        print(f"[context_bucket] Vision normalization failed: {e}")
        missing.append("image_input")

    a_context = None
    try:
        a_context = normalize_adapter(raw_adapter)
        if not a_context:
            missing.append("adapter_input")
    except Exception as e:
        print(f"[context_bucket] Adapter normalization failed: {e}")
        missing.append("adapter_input")

    # ── 2. Run Fusion Engine ──
    fusion, entries = run_fusion(v_context, vi_context, a_context)

    # ── 3. Build Canonical Context Metadata ──
    preliminary = _derive_preliminary_status(entries)
    overview = _generate_ai_overview(entries, fusion)
    
    crit = sum(1 for e in entries if e.severity_indication == "Critical")
    mod = sum(1 for e in entries if e.severity_indication == "Moderate")
    
    requires_review = any(e.technician_review_flag for e in entries)
    has_global_override = any(e.is_global_safety_override for e in entries)

    context = CanonicalInspectionContext(
        session_id=session_id,
        component_category=component_category,
        inspection_type=inspection_type,
        image_filename=image_filename,
        voice_context=v_context,
        vision_context=vi_context,
        adapter_context=a_context,
        adapter_version=adapter_version,
        fusion_result=fusion,
        context_entries=entries,
        preliminary_status=preliminary,
        critical_entry_count=crit,
        moderate_entry_count=mod,
        requires_technician_review=requires_review,
        ai_overview=overview,
        ai_priority_action="Evaluate all CRITICAL findings before operating." if crit > 0 else "Routine maintenance.",
        documentation_ready=bool(entries),
        missing_inputs=missing,
        downstream_hints={
            "report_template": "TA1" if inspection_type == "TA1" else "standard",
            "escalation_required": crit > 0,
            "global_safety_override_triggered": has_global_override,
            "adapter_override_triggered": (fusion.fusion_status in ["adapter_override", "adapter_conflict"])
        }
    )

    return context


def write_context_json(context: CanonicalInspectionContext, output_dir: str = "/outputs") -> str:
    """
    Writes context to output/{context_id}.json
    Returns the file path written.
    Uses forward slashes for Windows/Linux compatibility.
    """
    if not os.path.exists(output_dir):
        # Fallback to local 'output' if not running in Modal container
        if os.path.exists("output"):
            output_dir = "output"
        else:
            os.makedirs("output", exist_ok=True)
            output_dir = "output"
        
    path = f"{output_dir}/{context.context_id}.json"
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(context.to_json(indent=2))
        
    print(f"[context_bucket] Wrote context JSON to {path}")
        
    return path
