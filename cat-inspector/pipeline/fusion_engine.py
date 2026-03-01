from typing import Literal, Tuple, List, Optional
from schemas.context_schema import (
    NormalizedVoiceContext,
    NormalizedVisionContext,
    NormalizedAdapterContext,
    FusionResult,
    ContextBucketEntry
)

def run_fusion(
    voice: Optional[NormalizedVoiceContext],
    vision: Optional[NormalizedVisionContext],
    adapter: Optional[NormalizedAdapterContext] = None
) -> Tuple[FusionResult, List[ContextBucketEntry]]:
    """
    Three-way fusion logic.
    Adapter serves as an expert baseline against Voice (since it runs on voice transcript).
    """
    if not voice and not vision and not adapter:
        return (
            FusionResult(
                fusion_status="voice_only", # fallback spec
                agreement_score=0.0,
                reconciled_components=[],
                conflict_components=[],
                dominant_source="none",
                fusion_notes="All perceptor outputs were missing or invalid."
            ),
            []
        )

    entries = []
    reconciled = []
    used_vision_indices = set()
    e_counter = 1

    v_comps = voice.detected_components if voice else []
    
    # ── Voice-Vision Overlap & Voice-Only ──
    for v_comp in v_comps:
        overlapping_findings = []
        if vision:
            for idx, finding in enumerate(vision.findings):
                if v_comp.lower() in finding.component.lower() or finding.component.lower() in v_comp.lower():
                    overlapping_findings.append((idx, finding))
        
        if overlapping_findings:
            reconciled.append(v_comp)
            for idx, finding in overlapping_findings:
                used_vision_indices.add(idx)
                
                condition_aligns = False
                for cond in voice.detected_conditions:
                    if cond.lower() in finding.observation.lower():
                        condition_aligns = True
                        break
                        
                fusion_sev = finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"
                tech_flag = False
                ev_backed = False
                
                sources = ["voice", "vision"]
                ad_sev = None
                ad_ev = None
                conf_score = max(voice.language_confidence, vision.overall_confidence / 100.0)
                
                if condition_aligns:
                    ev_backed = True
                else:
                    tech_flag = True
                
                if adapter:
                    sources.append("adapter")
                    ad_sev = adapter.mapped_severity
                    ad_ev = adapter.raw_prediction
                    
                    if tech_flag:
                        if ad_sev != "Unknown":
                            fusion_sev = ad_sev 
                            tech_flag = False
                            conf_score = adapter.confidence
                    elif ad_sev == "Unknown" or ad_sev == fusion_sev:
                        pass
                    else:
                        tech_flag = True
                
                entries.append(ContextBucketEntry(
                    entry_id=f"FUS-{e_counter:03d}",
                    component=finding.component,
                    condition_summary=f"AI observed: {finding.observation}",
                    severity_indication=fusion_sev,
                    voice_evidence=voice.raw_transcript,
                    vision_evidence=finding.observation,
                    adapter_evidence=ad_ev,
                    adapter_severity=ad_sev,
                    evidence_backed=ev_backed,
                    technician_review_flag=tech_flag,
                    source_perceptors=sources,
                    confidence_score=conf_score,
                    is_global_safety_override=finding.is_global_safety_override,
                    global_override_category=finding.global_override_category
                ))
                e_counter += 1
        else:
            sources = ["voice"]
            fusion_sev = voice.inferred_severity
            ad_ev = None
            ad_sev = None
            conf_score = voice.language_confidence
            
            if adapter:
                sources.append("adapter")
                ad_ev = adapter.raw_prediction
                ad_sev = adapter.mapped_severity
                if ad_sev != "Unknown" and ad_sev != voice.inferred_severity:
                    fusion_sev = ad_sev
                    conf_score = adapter.confidence
                else:
                    conf_score = max(conf_score, adapter.confidence)
                    
            entries.append(ContextBucketEntry(
                entry_id=f"FUS-{e_counter:03d}",
                component=v_comp,
                condition_summary=f"Voice transcribed issue on the {v_comp}.",
                severity_indication=fusion_sev,
                voice_evidence=voice.raw_transcript,
                adapter_evidence=ad_ev,
                adapter_severity=ad_sev,
                evidence_backed=False,
                technician_review_flag=False,
                source_perceptors=sources,
                confidence_score=conf_score
            ))
            e_counter += 1

    # ── Vision-Only ──
    if vision:
        for idx, finding in enumerate(vision.findings):
            if idx not in used_vision_indices:
                sources = ["vision"]
                fusion_sev = finding.severity_indicator.capitalize() if finding.severity_indicator != "NORMAL" else "Normal"
                
                entries.append(ContextBucketEntry(
                    entry_id=f"FUS-{e_counter:03d}",
                    component=finding.component,
                    condition_summary=finding.observation,
                    severity_indication=fusion_sev,
                    vision_evidence=finding.observation,
                    evidence_backed=False,
                    technician_review_flag=False,
                    source_perceptors=sources,
                    confidence_score=vision.overall_confidence / 100.0,
                    is_global_safety_override=finding.is_global_safety_override,
                    global_override_category=finding.global_override_category
                ))
                e_counter += 1

    # ── Adapter-Only Fallback ──
    if not entries and adapter and adapter.mapped_severity != "Unknown":
        entries.append(ContextBucketEntry(
            entry_id=f"FUS-{e_counter:03d}",
            component="Adapter-Flagged-System",
            condition_summary="Adapter raised finding unconditionally.",
            severity_indication=adapter.mapped_severity,
            adapter_evidence=adapter.raw_prediction,
            adapter_severity=adapter.mapped_severity,
            evidence_backed=False,
            technician_review_flag=True,
            source_perceptors=["adapter"],
            confidence_score=adapter.confidence
        ))

    # ── Calculate Fusion Metadata ──
    vision_comps = [f.component for f in vision.findings] if vision else []
    all_unique = set(v_comps + vision_comps)
    total = len(all_unique)
    shared = len(reconciled)
    score = (shared / total) if total > 0 else 0.0

    if total == 0:
        if adapter:
            status = "adapter_override"
            notes = "Only adapter provided viable signal."
        else:
            status = "independent"
            notes = "No components identified by any source."
    elif shared == 0:
        if not voice and vision:
            status = "vision_only"
            notes = "Findings derived solely from visual inference."
        elif voice and not vision:
            status = "voice_only"
            notes = "Findings derived solely from technician STT."
        else:
            status = "independent"
            notes = "Voice and vision analyzed completely disperate components."
    elif any(e.technician_review_flag for e in entries):
        if adapter and all(e.adapter_severity != "Unknown" for e in entries if e.technician_review_flag and 'adapter' in e.source_perceptors):
             status = "adapter_conflict" 
             notes = f"Adapter attempted to resolve contradictions on {shared} shared components."
        else:
             status = "conflict"
             notes = f"Inputs overlapped on {shared} components but flagged contradictions requiring review."
    elif adapter and all('adapter' in e.source_perceptors for e in entries if 'voice' in e.source_perceptors):
        status = "three_way_agreement"
        notes = f"Strong alignment. {shared} components independently confirmed across perceptors."
    else:
        status = "full_agreement"
        notes = f"Strong alignment. {shared} components independently confirmed by AI modalities."

    fusion = FusionResult(
        fusion_status=status,
        agreement_score=score,
        reconciled_components=list(set(reconciled)),
        conflict_components=list(set([e.component for e in entries if e.technician_review_flag])),
        dominant_source="adapter" if (adapter and adapter.mapped_severity == "Critical") else ("equal" if score > 0.5 else ("vision" if len(vision_comps) > len(v_comps) else "voice")),
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
