from typing import Optional
from schemas.context_schema import (
    NormalizedVoiceContext,
    NormalizedVisionContext,
    VisionFinding
)

# Shared definitions for simplistic text mapping
D6N_COMPONENTS = {
    "track", "blade", "hydraulic", "engine", "final drive", "undercarriage",
    "sprocket", "idler", "roller", "cutting edge", "cooling hose", "radiator",
    "step", "handrail", "mirror", "rim", "tire", "lug nut", "wheel", "bolt",
    "bucket", "cab", "glass", "windshield", "door", "hinge", "latch"
}

CONDITION_KEYWORDS = {
    "leak", "leaking", "crack", "cracked", "broken", "bent", "missing", "loose",
    "worn", "wear", "rust", "corroded", "damaged", "flat", "torn", "seized",
    "overheating", "smoking", "grinding", "vibrating", "stuck", "low"
}

URGENT_WORDS = {"immediately", "critical", "stop", "broken", "leak", "missing", "severe", "danger", "unsafe", "cannot operate", "grounded"}
UNCERTAIN_WORDS = {"maybe", "possibly", "not sure", "hard to tell", "unclear", "might be", "could be", "appears to"}
ROUTINE_WORDS = {"check", "monitor", "schedule", "looks ok", "normal", "fine", "good", "no issues", "clean", "acceptable"}


def normalize_voice(raw_transcript: Optional[str]) -> Optional[NormalizedVoiceContext]:
    """
    Validates Whisper output. Extracts:
      - detected_components
      - detected_conditions
      - technician_sentiment
      - language_confidence (proxy)
    Returns None if transcript is empty or below 3 words.
    """
    if not raw_transcript:
        return None

    clean_text = raw_transcript.strip().lower()
    words = clean_text.split()
    
    if len(words) < 3:
        return None

    word_count = len(words)
    
    # ── Map components ──
    detected_components = []
    for comp in D6N_COMPONENTS:
        if comp in clean_text:
            detected_components.append(comp)

    # ── Map conditions ──
    detected_conditions = []
    for cond in CONDITION_KEYWORDS:
        if cond in clean_text:
            detected_conditions.append(cond)

    # ── Classify sentiment ──
    # Simple heuristic check priority
    sentiment = "routine"
    if any(u in clean_text for u in URGENT_WORDS):
        sentiment = "urgent"
    elif any(u in clean_text for u in UNCERTAIN_WORDS):
        sentiment = "uncertain"

    # ── Proxy confidence ──
    # Whisper base struggles mostly with mumbled/short snippets.
    # We assign confidence purely algorithmically lacking real token logprobs.
    base_conf = 0.85
    if word_count > 10:
        base_conf += 0.05
    if detected_components and detected_conditions:
        base_conf += 0.05
    if sentiment == "uncertain":
        base_conf -= 0.15
    
    conf = min(max(base_conf, 0.0), 1.0)

    return NormalizedVoiceContext(
        raw_transcript=raw_transcript.strip(),
        word_count=word_count,
        detected_components=detected_components,
        detected_conditions=detected_conditions,
        technician_sentiment=sentiment,
        language_confidence=conf
    )


def normalize_vision(raw_vision: Optional[dict]) -> Optional[NormalizedVisionContext]:
    """
    Validates Claude vision output dict.
    Derives critical_count and moderate_count from findings.
    Returns None if image_quality == "insufficient_lighting" AND confidence < 40.
    Returns vision context with empty findings if image_quality == "obstructed".
    """
    if not raw_vision:
        return None
        
    quality = raw_vision.get("image_quality", "clear")
    confidence = raw_vision.get("confidence", 0)
    
    if quality == "insufficient_lighting" and confidence < 40:
        return None

    # Handle obstruction edge case -> preserve context, wipe findings
    if quality == "obstructed":
        return NormalizedVisionContext(
            visible_components=raw_vision.get("visible_components", []),
            findings=[],
            overall_confidence=confidence,
            image_quality=quality,
            critical_count=0,
            moderate_count=0
        )

    # Build Pydantic models from raw dicts
    findings = []
    crit_count = 0
    mod_count = 0
    
    for f_raw in raw_vision.get("findings", []):
        try:
            finding = VisionFinding(**f_raw)
            findings.append(finding)
            
            if finding.severity_indicator == "CRITICAL":
                crit_count += 1
            elif finding.severity_indicator == "MODERATE":
                mod_count += 1
        except Exception as e:
            print(f"[normalizer] Dropped invalid finding during normalization: {e}")

    return NormalizedVisionContext(
        visible_components=raw_vision.get("visible_components", []),
        findings=findings,
        overall_confidence=confidence,
        image_quality=quality,
        critical_count=crit_count,
        moderate_count=mod_count
    )
