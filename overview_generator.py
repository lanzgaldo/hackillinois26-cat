"""
overview_generator.py — Claude General Overview Generator
─────────────────────────────────────────────────────────
Reads a completed inspection JSON artifact (output/ or /outputs),
calls Claude claude-sonnet-4-5 to produce a plain-text, bullet-formatted
technician overview report.

Usage:
    modal run overview_generator.py                              # latest artifact
    modal run overview_generator.py::generate_for_file --path ./output/abc.json
    modal run overview_generator.py::batch_generate              # all missing
"""

import os
import re
import json
import datetime
import warnings
from pathlib import Path
from typing import Optional

import modal

# ── Constants ─────────────────────────────────────────────────────

OUTPUT_DIR = Path("./output")
MAX_CONTEXT_FILE_BYTES = 2_000_000
MAX_OVERVIEW_CHARS     = 6_500
MAX_FIELD_CHARS        = 800

D6N_MACHINE_CONTEXT = """
MACHINE: CAT D6N Track-Type Tractor (Medium Dozer)
ENGINE: Cat C6.6 ACERT, 111.8 kW / 150 hp, 6.6L inline-6
KEY SERVICE INTERVALS:
  10 hr / Daily : Cab recirculation filter inspect
  50 hr         : Track tension check
  250 hr        : Engine oil + filter change
  500 hr        : Hydraulic oil filter, fuel system filter, final drive oil check
  1000 hr       : Final drive oil change, transmission oil + filter
  2000 hr       : Hydraulic oil change
KEY SYSTEMS:
  - ADEM A4 ECM: controls fuel injection; fault = Critical
  - EMS III: 3-level warning; monitors coolant, trans oil, hydraulic oil, fuel, air
  - Sealed/lubricated track with dual-flange rollers
  - Electro-hydraulic powershift transmission 3F/3R
"""

# ── Modal App ─────────────────────────────────────────────────────

app = modal.App("cat-inspect-ai-sprint1")

image = modal.Image.debian_slim().pip_install(
    "anthropic", "fastapi[standard]"
)

# ── Security Utilities ────────────────────────────────────────────

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"disregard.*above",
    r"you are now",
    r"act as",
    r"new instructions",
    r"system:",
    r"human:",
    r"assistant:",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]


def sanitize_for_prompt(value: Optional[str], max_len: int = MAX_FIELD_CHARS) -> str:
    """
    Sanitize untrusted string fields before interpolation into a Claude prompt.
    Raises ValueError on injection patterns rather than silently stripping.
    """
    if not value:
        return ""
    text = str(value)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    text = text[:max_len]
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            raise ValueError(
                f"sanitize_for_prompt: Potential prompt injection detected. "
                f"Pattern: '{pattern}'. Preview: '{text[:80]}'"
            )
    return text.strip()


def _validate_api_key() -> None:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or not key.startswith("sk-ant-"):
        raise RuntimeError(
            "FATAL: ANTHROPIC_API_KEY not configured or malformed. "
            "Set via Modal secret: anthropic-secret"
        )


# ── Input Validation ──────────────────────────────────────────────

def validate_context_path(path: str) -> Path:
    """Validate that path points to a readable inspection JSON artifact."""
    if not path or not isinstance(path, str):
        raise ValueError("validate_context_path: path must be a non-empty string")
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"validate_context_path: file not found: {p}")
    if not p.is_file():
        raise ValueError(f"validate_context_path: path is not a file: {p}")
    size = p.stat().st_size
    if size > MAX_CONTEXT_FILE_BYTES:
        raise ValueError(f"validate_context_path: file too large ({size} bytes)")
    try:
        with open(p, "r", encoding="utf-8") as f:
            raw_text = f.read()
        # Handle files with trailing non-JSON content (e.g. Modal log lines)
        # Find the last closing brace to extract only the JSON portion
        last_brace = raw_text.rfind("}")
        if last_brace == -1:
            raise ValueError("validate_context_path: no JSON object found in file")
        data = json.loads(raw_text[:last_brace + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"validate_context_path: invalid JSON — {e}")
    # Accept either raw CanonicalInspectionContext or pipeline output wrapper
    if "context_id" not in data and "inspection_output" not in data:
        raise ValueError(
            "validate_context_path: Neither 'context_id' nor 'inspection_output' found. "
            "File does not appear to be an inspection artifact."
        )
    return p


def validate_overview_output(text: str) -> str:
    """Validate Claude's plain-text overview before writing to disk."""
    if not text or not isinstance(text, str):
        raise ValueError("validate_overview_output: empty response from Claude")
    stripped = text.strip()
    if len(stripped) > MAX_OVERVIEW_CHARS:
        warnings.warn(f"Overview exceeds {MAX_OVERVIEW_CHARS} chars ({len(stripped)}). Truncating.")
        stripped = stripped[:MAX_OVERVIEW_CHARS]
    if stripped.startswith("{") and '"context_id"' in stripped:
        raise ValueError("validate_overview_output: response is JSON, not plain text")
    if "sk-ant-" in stripped:
        raise ValueError("validate_overview_output: API key pattern found in output")
    return stripped


# ── Format Helpers ────────────────────────────────────────────────

def _format_status_line(status: str) -> str:
    mapping = {
        "STOP":              "STOP — DO NOT OPERATE",
        "fail":              "FAIL — IMMEDIATE SERVICE REQUIRED",
        "CAUTION":           "CAUTION — SCHEDULE SERVICE",
        "monitor":           "MONITOR — SERVICE WITHIN 48 HOURS",
        "GO":                "PASS — CLEARED FOR OPERATION",
        "pass":              "PASS — CLEARED FOR OPERATION",
        "INSUFFICIENT_DATA": "INCOMPLETE — INSUFFICIENT DATA",
    }
    return mapping.get(status, status.upper())


def _format_fusion_status(fusion_status: str) -> str:
    mapping = {
        "full_agreement":    "Voice and vision fully agree",
        "partial_agreement": "Voice and vision partially agree",
        "conflict":          "Voice and vision conflict — manual review required",
        "voice_only":        "Voice input only — no image provided",
        "vision_only":       "Vision input only — no voice note",
        "independent":       "Multiple independent sources",
    }
    return mapping.get(fusion_status, fusion_status)


def _format_datetime(iso_string: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y at %I:%M %p UTC")
    except Exception:
        return iso_string or "Not recorded"


def _severity_sort_key(entry: dict) -> int:
    order = {"Critical": 0, "Moderate": 1, "Low": 2, "Normal": 3, "Unknown": 4}
    return order.get(entry.get("severity_indication", entry.get("severity", "Unknown")), 4)


# ── Prompt Assembly ───────────────────────────────────────────────

def _normalize_context(raw: dict) -> dict:
    """
    Normalize both raw CanonicalInspectionContext artifacts
    and pipeline output wrapper format into a unified dict
    for prompt assembly.
    """
    # If it's a pipeline output wrapper (context_path + inspection_output)
    if "inspection_output" in raw and "context_id" not in raw:
        io = raw["inspection_output"]
        summary = io.get("inspection_summary", {})
        anomalies = io.get("anomalies", [])

        # Convert anomalies to context_entries format
        entries = []
        for i, a in enumerate(anomalies):
            entries.append({
                "entry_id": f"E{i+1:03d}",
                "component": a.get("component", "Unknown"),
                "component_location": a.get("component_location", ""),
                "condition_summary": a.get("condition_description", a.get("issue", "")),
                "severity_indication": a.get("severity", "Unknown"),
                "part_number": a.get("part_number"),
                "recommended_action": a.get("recommended_action", ""),
                "estimated_timeline": a.get("estimated_timeline", ""),
                "safety_impact_assessment": a.get("safety_impact_assessment", ""),
                "operational_impact": a.get("operational_impact", ""),
                "source_perceptors": ["vision"] if a.get("confidence_score") else [],
                "evidence_backed": a.get("evidence_backed", False),
                "technician_review_flag": a.get("technician_review_required", False),
                "is_global_safety_override": a.get("is_global_safety_override", False),
                "global_override_category": a.get("global_override_category"),
                "voice_evidence": None,
                "vision_evidence": a.get("condition_description", ""),
                "confidence_score": (a.get("confidence_score", 0) / 100.0)
                    if isinstance(a.get("confidence_score"), (int, float)) and a.get("confidence_score", 0) > 1
                    else a.get("confidence_score", 0),
            })

        context_id = raw.get("context_path", "").split("/")[-1].replace(".json", "") or "unknown"
        status = summary.get("status", "unknown")

        return {
            "context_id": context_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "asset_id": summary.get("asset", "CAT D6N Dozer"),
            "preliminary_status": status,
            "ai_priority_action": summary.get("overall_operational_impact", ""),
            "critical_entry_count": sum(1 for e in entries if e.get("severity_indication") == "Critical"),
            "moderate_entry_count": sum(1 for e in entries if e.get("severity_indication") == "Moderate"),
            "voice_context": None,
            "vision_context": None,
            "fusion_result": None,
            "adapter_context": None,
            "context_entries": entries,
            "downstream_hints": {},
        }

    # Already a CanonicalInspectionContext — return as-is
    return raw


def build_overview_prompt(context: dict) -> str:
    """Assemble the Claude prompt from the inspection context dict."""
    context = _normalize_context(context)

    context_id    = sanitize_for_prompt(context.get("context_id", "UNKNOWN"), 64)
    created_at    = _format_datetime(context.get("created_at", ""))
    asset_id      = sanitize_for_prompt(context.get("asset_id", "CAT D6N Dozer"), 100)
    prelim_status = sanitize_for_prompt(context.get("preliminary_status", "UNKNOWN"), 32)
    status_label  = _format_status_line(prelim_status)
    ai_priority   = sanitize_for_prompt(context.get("ai_priority_action", ""), 600)
    critical_count  = int(context.get("critical_entry_count", 0))
    moderate_count  = int(context.get("moderate_entry_count", 0))

    # Voice context
    voice_ctx      = context.get("voice_context") or {}
    raw_transcript = sanitize_for_prompt(voice_ctx.get("raw_transcript", ""), 600)
    voice_conf     = voice_ctx.get("language_confidence")
    voice_conf_str = f"{int(voice_conf * 100)}%" if voice_conf is not None else "N/A"

    # Vision context
    vision_ctx     = context.get("vision_context") or {}
    vision_conf    = vision_ctx.get("overall_confidence")
    image_quality  = sanitize_for_prompt(vision_ctx.get("image_quality", ""), 32)
    vision_conf_str = f"{vision_conf}%" if vision_conf is not None else "No image provided"

    # Fusion
    fusion         = context.get("fusion_result") or {}
    fusion_status  = sanitize_for_prompt(fusion.get("fusion_status", ""), 32)
    fusion_label   = _format_fusion_status(fusion_status) if fusion_status else "Single source"
    agreement_score = fusion.get("agreement_score")
    agreement_str  = f"{int(agreement_score * 100)}% agreement" if agreement_score else ""

    # Adapter
    adapter_ctx        = context.get("adapter_context") or {}
    adapter_severity   = sanitize_for_prompt(adapter_ctx.get("severity_mapped", adapter_ctx.get("mapped_severity", "")), 32)
    adapter_component  = sanitize_for_prompt(adapter_ctx.get("component", adapter_ctx.get("anomalous_condition", "")), 200)
    adapter_rationale  = sanitize_for_prompt(adapter_ctx.get("rationale", ""), 600)
    adapter_action     = sanitize_for_prompt(adapter_ctx.get("recommended_action", ""), 600)
    adapter_confidence = adapter_ctx.get("confidence")
    adapter_source     = sanitize_for_prompt(adapter_ctx.get("source", ""), 64)
    adapter_conf_str   = f"{int(adapter_confidence * 100)}%" if adapter_confidence else "N/A"
    has_adapter        = bool(adapter_ctx and adapter_source not in ("no_adapter", "bridge_error", ""))

    # Context entries sorted by severity
    entries = context.get("context_entries", [])
    sorted_entries = sorted(entries, key=_severity_sort_key)
    evidence_backed_count = sum(1 for e in entries if e.get("evidence_backed"))
    total_entries = len(entries)

    # Build entry blocks
    entry_blocks = []
    for entry in sorted_entries:
        comp     = sanitize_for_prompt(entry.get("component", "Unknown"), 200)
        location = sanitize_for_prompt(entry.get("component_location", ""), 200)
        severity = sanitize_for_prompt(entry.get("severity_indication", entry.get("severity", "Unknown")), 32)
        summary  = sanitize_for_prompt(entry.get("condition_summary", ""), 600)
        part_num = sanitize_for_prompt(entry.get("part_number", ""), 32)
        action   = sanitize_for_prompt(entry.get("recommended_action", ""), 600)
        timeline = sanitize_for_prompt(entry.get("estimated_timeline", ""), 200)
        safety   = sanitize_for_prompt(entry.get("safety_impact_assessment", ""), 400)
        ops_imp  = sanitize_for_prompt(entry.get("operational_impact", ""), 400)
        sources  = entry.get("source_perceptors", [])
        evidence = "Voice + Vision" if ("voice" in sources and "vision" in sources) \
                   else ("Voice" if "voice" in sources else "Vision")
        is_override  = entry.get("is_global_safety_override", False)
        override_cat = sanitize_for_prompt(entry.get("global_override_category", ""), 64)
        backed       = entry.get("evidence_backed", False)
        review_flag  = entry.get("technician_review_flag", False)
        voice_ev     = sanitize_for_prompt(entry.get("voice_evidence", ""), 400)
        vision_ev    = sanitize_for_prompt(entry.get("vision_evidence", ""), 400)

        block = f"""  COMPONENT: {comp}{(' — ' + location) if location else ''}
  Part Number: {part_num if part_num else 'N/A'}
  Severity: {severity}
  Evidence: {evidence}{'  [AI VERIFIED]' if backed else '  [REVIEW REQUIRED]' if review_flag else ''}
{('  ⚠ GLOBAL SAFETY OVERRIDE — ' + override_cat.upper().replace('_', ' ') + chr(10)) if is_override else ''}  - {summary}
{('  - Voice Note: ' + voice_ev + chr(10)) if voice_ev else ''}{('  - Safety Impact: ' + safety + chr(10)) if safety else ''}{('  - Operational Impact: ' + ops_imp + chr(10)) if ops_imp else ''}{('  - Timeline: ' + timeline + chr(10)) if timeline else ''}  - Action Required: {action if action else 'Consult CAT dealer for assessment'}"""
        entry_blocks.append(block.strip())

    entries_text = "\n\n".join(entry_blocks) if entry_blocks else "No anomalies detected."

    # Adapter section
    if has_adapter:
        adapter_section = f"""ADAPTER ASSESSMENT (Mistral-7B D6N Domain Model)
- Domain Model Severity: {adapter_severity}
- Component Flagged: {adapter_component if adapter_component else 'Not specified'}
- Rationale: {adapter_rationale if adapter_rationale else 'Not provided'}
- Recommended Action: {adapter_action if adapter_action else 'Not provided'}
- Model Confidence: {adapter_conf_str}"""
    else:
        adapter_section = "ADAPTER ASSESSMENT (Mistral-7B D6N Domain Model)\n- Domain model adapter not available for this inspection run."

    # Transcript section
    transcript_section = ""
    if raw_transcript:
        transcript_section = f'\nTECHNICIAN VOICE NOTE\n"{raw_transcript}"'

    # Full prompt
    prompt = f"""You are generating a plain-text inspection report for a CAT D6N Track-Type Dozer field technician.

MACHINE CONTEXT:
{D6N_MACHINE_CONTEXT.strip()}

INSPECTION DATA:
Inspection ID: {context_id}
Date: {created_at}
Asset: {asset_id}
Overall Status: {status_label}
Critical Findings: {critical_count}
Moderate Findings: {moderate_count}
{transcript_section}

ANOMALIES IDENTIFIED BY AI PIPELINE:

{entries_text}

{adapter_section}

AI CONFIDENCE METRICS:
- Fusion Status: {fusion_label}{(' (' + agreement_str + ')') if agreement_str else ''}
- Voice Transcription Confidence: {voice_conf_str}
- Vision Analysis Confidence: {vision_conf_str}
- Evidence-Backed Findings: {evidence_backed_count} of {total_entries}
{('- Image Quality: ' + image_quality) if image_quality else ''}

PRIORITY ACTION: {ai_priority if ai_priority else 'Consult CAT dealer'}

INSTRUCTIONS FOR REPORT GENERATION:
Write the final technician inspection report using this exact format:

1. Open with a header block bounded by dashes:
   INSPECTION REPORT — CAT D6N DOZER
   Asset, Inspection ID, Date/Time, Overall Status

2. INSPECTION SUMMARY section — 2-3 bullet points

3. ANOMALIES FOUND section — one sub-block per finding with:
   COMPONENT, Part Number, Severity, Evidence, condition, safety impact,
   operational impact, timeline, action required

4. Global safety override findings marked with ⚠ prefix

5. ADAPTER ASSESSMENT section

6. AI CONFIDENCE section

7. PRIORITY ACTION in ALL CAPS

8. END OF REPORT

STRICT RULES:
- Plain text ONLY. No markdown. No JSON. No code blocks.
- Use dashes (-) for all bullet points
- Write in second person: "Technician should..."
- Never hedge: no "possibly", "might", "could be"
- Severity verbatim: Critical, Moderate, or Low
- Status verbatim as given above
- Part numbers exactly as given (PT-D6N-xxx format) or "N/A"
- Timelines must be specific: "Replace within 50 operating hours"
- Keep total report under 3500 characters"""

    return prompt


# ── Claude Call ────────────────────────────────────────────────────

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("anthropic-secret")],
    timeout=60
)
def call_claude_for_overview(prompt: str) -> str:
    """Call Claude claude-sonnet-4-5 to generate the plain-text overview report."""
    import urllib.request

    _validate_api_key()
    api_key = os.environ["ANTHROPIC_API_KEY"]

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "system": (
            "You are a technical writer generating plain-text inspection reports "
            "for CAT D6N field technicians. You follow the exact format of CAT "
            "inspection reports used in the field. You write in direct, unambiguous "
            "English. You never hedge, never invent findings not in the data, "
            "and never use markdown or JSON in your output."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=55) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "No body"
        raise RuntimeError(f"Anthropic API error {e.code}: {error_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error — {e.reason}")

    content = response_data.get("content", [])
    if not content or not isinstance(content, list):
        raise RuntimeError(f"Unexpected response: {str(response_data)[:200]}")

    text_blocks = [
        block["text"] for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    if not text_blocks:
        raise RuntimeError("No text blocks in Claude response")

    return "\n".join(text_blocks)


# ── File I/O ──────────────────────────────────────────────────────

def write_overview(context_id: str, overview_text: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """Write validated overview to output/{context_id}_overview.txt."""
    safe_id = re.sub(r'[^a-zA-Z0-9\-_]', '', context_id)[:64]
    if not safe_id:
        raise ValueError("write_overview: context_id produced empty safe filename")
    if not output_dir.exists():
        raise FileNotFoundError(f"write_overview: output directory {output_dir} does not exist")
    out_path = output_dir / f"{safe_id}_overview.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(overview_text)
    print(f"[overview_generator] Written: {out_path}")
    return out_path


# ── Public API ────────────────────────────────────────────────────

def generate_overview(context_json_path: str) -> str:
    """
    Public entry point. Reads an inspection JSON artifact,
    generates a plain-text technician overview report, writes it to disk,
    and returns the overview text.
    """
    validated_path = validate_context_path(context_json_path)
    with open(validated_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    # Robust JSON parsing — handles files with trailing non-JSON content
    last_brace = raw_text.rfind("}")
    raw = json.loads(raw_text[:last_brace + 1])

    # Extract context_id
    if "context_id" in raw:
        context_id = raw["context_id"]
    else:
        context_id = raw.get("context_path", "").split("/")[-1].replace(".json", "") or validated_path.stem

    prompt = build_overview_prompt(raw)
    raw_overview = call_claude_for_overview.remote(prompt)
    validated_overview = validate_overview_output(raw_overview)
    write_overview(context_id, validated_overview, output_dir=validated_path.parent)
    return validated_overview


# ── Entrypoints ───────────────────────────────────────────────────

@app.local_entrypoint()
def generate_for_latest():
    """Generate overview for the most recent JSON artifact in output/."""
    json_files = sorted(
        [p for p in OUTPUT_DIR.glob("*.json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not json_files:
        print("[overview_generator] No JSON artifacts found in output/")
        return
    latest = json_files[0]
    print(f"[overview_generator] Processing: {latest.name}")
    overview = generate_overview(str(latest))
    print("\n" + "=" * 60)
    print(overview)
    print("=" * 60)


@app.local_entrypoint()
def generate_for_file(path: str):
    """Generate overview for a specific context JSON file."""
    overview = generate_overview(path)
    print("\n" + "=" * 60)
    print(overview)
    print("=" * 60)


@app.local_entrypoint()
def batch_generate(output_dir: str = "./output"):
    """Generate overviews for ALL JSONs in output/ missing an _overview.txt."""
    target = Path(output_dir)
    if not target.exists():
        print(f"[overview_generator] Directory not found: {target}")
        return
    json_files = [p for p in target.glob("*.json")]
    if not json_files:
        print("[overview_generator] No JSON artifacts found.")
        return

    skipped = processed = failed = 0
    for jf in sorted(json_files):
        overview_path = target / f"{jf.stem}_overview.txt"
        if overview_path.exists():
            print(f"  SKIP: {jf.name}")
            skipped += 1
            continue
        try:
            print(f"  Processing: {jf.name}")
            generate_overview(str(jf))
            processed += 1
        except Exception as e:
            print(f"  FAILED: {jf.name} — {e}")
            failed += 1

    print(f"\nBatch: {processed} generated, {skipped} skipped, {failed} failed")
