import json
import os
from datetime import datetime, timezone
from typing import Optional, Literal
from schemas.context_schema import CanonicalInspectionContext
from pipeline.perceptor_normalizer import normalize_voice, normalize_vision
from pipeline.fusion_engine import run_fusion, _derive_preliminary_status, _generate_ai_overview

async def build_context_bucket(
    raw_transcript: Optional[str] = None,
    raw_vision: Optional[dict] = None,
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

    # ── 2. Run Fusion Engine ──
    fusion, entries = run_fusion(v_context, vi_context)

    # ── 3. Build Canonical Context Metadata ──
    preliminary = _derive_preliminary_status(entries)
    overview = _generate_ai_overview(entries, fusion)
    
    crit = sum(1 for e in entries if e.severity_indication == "Critical")
    mod = sum(1 for e in entries if e.severity_indication == "Moderate")
    
    requires_review = any(e.technician_review_flag for e in entries)

    context = CanonicalInspectionContext(
        session_id=session_id,
        component_category=component_category,
        inspection_type=inspection_type,
        image_filename=image_filename,
        voice_context=v_context,
        vision_context=vi_context,
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
            "escalation_required": crit > 0
        }
    )

    return context


def write_context_json(context: CanonicalInspectionContext, output_dir: str = "output") -> str:
    """
    Writes context to output/{context_id}.json
    Returns the file path written.
    Uses forward slashes for Windows/Linux compatibility.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    path = f"{output_dir}/{context.context_id}.json"
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(context.to_json(indent=2))
        
    return path
