from typing import Literal, Tuple, List, Optional
from schemas.context_schema import (
    NormalizedVoiceContext,
    NormalizedVisionContext,
    FusionResult,
    ContextBucketEntry
)

def run_fusion(
    voice: Optional[NormalizedVoiceContext],
    vision: Optional[NormalizedVisionContext]
) -> Tuple[FusionResult, List[ContextBucketEntry]]:
    """
    Fusion logic rules:
      CASE 1 — Both present, components overlap (agreements and conflicts)
      CASE 2 — Both present, no component overlap (independent)
      CASE 3 — Voice only
      CASE 4 — Vision only
      CASE 5 — Both None
    """
    # ── CASE 5: Both None ──
    if not voice and not vision:
        return (
            FusionResult(
                fusion_status="voice_only", # As per spec 
                agreement_score=0.0,
                reconciled_components=[],
                conflict_components=[],
                dominant_source="none",
                fusion_notes="Both perceptor outputs were missing or invalid."
            ),
            []
        )

    # ── CASE 3: Voice Only ──
    if voice and not vision:
        entries = []
        for i, comp in enumerate(voice.detected_components):
            entries.append(ContextBucketEntry(
                entry_id=f"VCE-{i+1:03d}",
                component=comp,
                condition_summary=f"Voice transcribed issue on the {comp}.",
                severity_indication=voice.inferred_severity,
                voice_evidence=voice.raw_transcript,
                evidence_backed=False,
                technician_review_flag=False,
                source_perceptors=["voice"],
                confidence_score=voice.language_confidence
            ))
        return (
            FusionResult(
                fusion_status="voice_only",
                agreement_score=0.0,
                reconciled_components=[],
                conflict_components=[],
                dominant_source="voice",
                fusion_notes="Vision input unavailable. Findings derived solely from technician STT."
            ),
            entries
        )

    # ── CASE 4: Vision Only ──
    if vision and not voice:
        entries = []
        for i, finding in enumerate(vision.findings):
            entries.append(ContextBucketEntry(
                entry_id=f"VIS-{i+1:03d}",
                component=finding.component,
                condition_summary=finding.observation,
                severity_indication=(finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"),
                vision_evidence=finding.observation,
                evidence_backed=False,
                technician_review_flag=False,
                source_perceptors=["vision"],
                confidence_score=vision.overall_confidence / 100.0
            ))
        return (
            FusionResult(
                fusion_status="vision_only",
                agreement_score=0.0,
                reconciled_components=[],
                conflict_components=[],
                dominant_source="vision",
                fusion_notes="Voice input unavailable. Findings derived solely from visual inference."
            ),
            entries
        )

    # ── CASE 1 & 2: Both Present ──
    assert voice is not None
    assert vision is not None

    entries = []
    reconciled = []
    conflicts = []
    
    # Track used vision findings so we can add the unseen ones later
    used_vision_indices = set()
    e_counter = 1

    for v_comp in voice.detected_components:
        # Does this voice component overlap with ANY vision components?
        # We perform simple substring matching for the proof of concept.
        overlapping_findings = []
        for idx, finding in enumerate(vision.findings):
            if v_comp.lower() in finding.component.lower() or finding.component.lower() in v_comp.lower():
                overlapping_findings.append((idx, finding))
                
        if overlapping_findings:
            # Overlap found!
            reconciled.append(v_comp)
            for idx, finding in overlapping_findings:
                used_vision_indices.add(idx)
                
                # Check condition alignment (very basic keyword overlap check)
                condition_aligns = False
                for cond in voice.detected_conditions:
                    if cond.lower() in finding.observation.lower():
                        condition_aligns = True
                        break
                        
                if condition_aligns:
                    # TRUE AGREEMENT
                    entries.append(ContextBucketEntry(
                        entry_id=f"FUS-{e_counter:03d}",
                        component=finding.component,
                        condition_summary=f"Confirmed {finding.observation} ({finding.severity_indicator.capitalize()})",
                        severity_indication=(finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"),
                        voice_evidence=voice.raw_transcript,
                        vision_evidence=finding.observation,
                        evidence_backed=True,
                        technician_review_flag=False,
                        source_perceptors=["voice", "vision"],
                        confidence_score=max(voice.language_confidence, vision.overall_confidence / 100.0),
                        is_global_safety_override=finding.is_global_safety_override,
                        global_override_category=finding.global_override_category
                    ))
                else:
                    # CONTRADICTION / PARTIAL
                    conflicts.append(v_comp)
                    entries.append(ContextBucketEntry(
                        entry_id=f"FUS-{e_counter:03d}",
                        component=finding.component,
                        condition_summary=f"AI observed: {finding.observation}. Tech notes unaligned.",
                        severity_indication=(finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"),
                        voice_evidence=voice.raw_transcript,
                        vision_evidence=finding.observation,
                        evidence_backed=False,
                        technician_review_flag=True,
                        source_perceptors=["voice", "vision"],
                        confidence_score=vision.overall_confidence / 100.0,
                        is_global_safety_override=finding.is_global_safety_override,
                        global_override_category=finding.global_override_category
                    ))
                e_counter += 1
        else:
            # NO OVERLAP for this voice component
            entries.append(ContextBucketEntry(
                entry_id=f"FUS-{e_counter:03d}",
                component=v_comp,
                condition_summary=f"Voice transcribed issue on the {v_comp}.",
                severity_indication=voice.inferred_severity,
                voice_evidence=voice.raw_transcript,
                evidence_backed=False,
                technician_review_flag=False,
                source_perceptors=["voice"],
                confidence_score=voice.language_confidence
            ))
            e_counter += 1

    # Add remaining vision findings
    for idx, finding in enumerate(vision.findings):
        if idx not in used_vision_indices:
            entries.append(ContextBucketEntry(
                entry_id=f"FUS-{e_counter:03d}",
                component=finding.component,
                condition_summary=finding.observation,
                severity_indication=(finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"),
                vision_evidence=finding.observation,
                evidence_backed=False,
                technician_review_flag=False,
                source_perceptors=["vision"],
                confidence_score=vision.overall_confidence / 100.0
            ))
            e_counter += 1

    # ── Calculate Fusion Metadata ──
    all_unique = set(voice.detected_components + [f.component for f in vision.findings])
    total = len(all_unique)
    shared = len(reconciled)
    score = (shared / total) if total > 0 else 0.0

    if total == 0:
        status = "independent"
        notes = "No components identified by either source."
    elif shared == 0:
        status = "independent"
        notes = "Voice and vision analyzed completely disperate components."
    elif conflicts:
        status = "conflict" if len(conflicts) > len(reconciled) else "partial_agreement"
        notes = f"Inputs overlapped on {shared} components but flagged {len(conflicts)} contradictions requiring review."
    else:
        status = "full_agreement"
        notes = f"Strong alignment. {shared} components were independently confirmed by both AI modalities."

    fusion = FusionResult(
        fusion_status=status,
        agreement_score=score,
        reconciled_components=list(set(reconciled)),
        conflict_components=list(set(conflicts)),
        dominant_source="equal" if score > 0.5 else ("vision" if len(vision.findings) > len(voice.detected_components) else "voice"),
        fusion_notes=notes
    )

    return fusion, entries


def _derive_preliminary_status(entries: List[ContextBucketEntry]) -> Literal["STOP", "CAUTION", "GO", "INSUFFICIENT_DATA"]:
    if not entries:
        return "INSUFFICIENT_DATA"
    
    has_moderate = False
    for e in entries:
        if e.severity_indication == "Critical":
            return "STOP"
        if e.severity_indication == "Moderate":
            has_moderate = True
            
    return "CAUTION" if has_moderate else "GO"


def _generate_ai_overview(entries: List[ContextBucketEntry], fusion: FusionResult) -> str:
    if not entries:
        return "No actionable anomalies were detected in the provided inputs. Evaluation aborted."

    comps = list({e.component for e in entries})
    comp_str = "various components" if len(comps) > 3 else " and ".join(comps)
    
    crit = sum(1 for e in entries if e.severity_indication == "Critical")
    mod = sum(1 for e in entries if e.severity_indication == "Moderate")

    crit_entry = next((e for e in entries if e.severity_indication == "Critical"), None)
    mod_entry = next((e for e in entries if e.severity_indication == "Moderate"), None)
    
    urgent = ""
    if crit_entry:
        urgent = f"Immediate attention needed for {crit_entry.component}: {crit_entry.condition_summary}."
    elif mod_entry:
        urgent = f"Highest priority finding on {mod_entry.component}: {mod_entry.condition_summary}."
    else:
        urgent = "All findings appear routine."

    return f"Inspection of {comp_str} found {crit} critical and {mod} moderate anomalies. {urgent} {fusion.fusion_notes}"
