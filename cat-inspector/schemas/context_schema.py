import uuid
from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# MODEL 1 — NormalizedVoiceContext
# ─────────────────────────────────────────────────────────────

class NormalizedVoiceContext(BaseModel):
    """
    Validated output from the voice perceptor (Whisper STT).
    Raw transcript cleaned and enriched with extracted metadata.
    """
    raw_transcript:       str = Field(..., description="The exact transcription text from Whisper")
    word_count:           int = Field(..., description="Computed number of words in the transcript")
    detected_components:  list[str] = Field(default_factory=list, description="Machine components referenced in the audio")
    detected_conditions:  list[str] = Field(default_factory=list, description="Conditions or damage identifiers referenced")
    technician_sentiment: Literal["urgent", "routine", "uncertain"] = Field(..., description="Classification of technician's tone/urgency")
    inferred_severity:    Literal["Critical", "Moderate", "Low", "Normal"] = Field(..., description="Fact-based severity derived from the transcript")
    language_confidence:  float = Field(..., ge=0.0, le=1.0, description="Proxy for whisper transcription confidence quality")
    source:               Literal["voice"] = Field(default="voice", description="Always 'voice'")


# ─────────────────────────────────────────────────────────────
# MODEL 2 — NormalizedVisionContext
# ─────────────────────────────────────────────────────────────

class VisionFinding(BaseModel):
    """A single finding identified by Claude Vision."""
    component:          str = Field(..., description="Name of the part")
    observation:        str = Field(..., description="What was visually observed")
    severity_indicator: Literal["CRITICAL", "MODERATE", "LOW", "NORMAL"] = Field(..., description="Predicted severity level")
    is_global_safety_override: bool = Field(default=False)
    segment_mismatch_flag: bool = Field(default=False)
    global_override_category: Optional[str] = Field(default=None)


class NormalizedVisionContext(BaseModel):
    """
    Validated output from the image perceptor (Claude Vision).
    Raw vision dict normalized into typed structure.
    """
    visible_components:  list[str] = Field(default_factory=list, description="All components actively visible in frame")
    findings:            list[VisionFinding] = Field(default_factory=list, description="Specific defects or conditions noted")
    overall_confidence:  int = Field(..., ge=0, le=100, description="AI confidence in its visual breakdown 0-100")
    image_quality:       Literal["clear", "obstructed", "insufficient_lighting"] = Field(..., description="Quality assessment of the source image")
    critical_count:      int = Field(..., description="Quantity of CRITICAL findings")
    moderate_count:      int = Field(..., description="Quantity of MODERATE findings")
    source:              Literal["vision"] = Field(default="vision", description="Always 'vision'")


# ─────────────────────────────────────────────────────────────
# MODEL 2.5 — NormalizedAdapterContext
# ─────────────────────────────────────────────────────────────

class NormalizedAdapterContext(BaseModel):
    """
    Validated output from the local Mistral-7B adapter.
    """
    raw_prediction:        str = Field(..., description="The raw string output from the adapter")
    mapped_severity:       Literal["Critical", "Moderate", "Normal", "Unknown"] = Field(..., description="Mapped severity from prediction")
    confidence:            float = Field(..., ge=0.0, le=1.0, description="Adapter certainty score")
    anomalous_condition:   Optional[str] = Field(default=None, description="Extracted condition string if available")
    source:                Literal["adapter", "no_adapter"] = Field(default="adapter", description="Source identifier or fallback")



# ─────────────────────────────────────────────────────────────
# MODEL 3 — FusionResult
# ─────────────────────────────────────────────────────────────

class FusionResult(BaseModel):
    """
    Output of the fusion engine. Describes the reconciled
    relationship between voice and vision perceptor outputs.
    """
    fusion_status: Literal[
        "full_agreement",      # voice + vision identify same component + condition
        "three_way_agreement", # voice + vision + adapter all agree
        "partial_agreement",   # same component, different severity or condition
        "conflict",            # contradicting findings on same component
        "adapter_conflict",    # adapter strongly disagrees with voice/vision
        "adapter_override",    # adapter provided the only viable signal
        "voice_only",          # no image/adapter provided or image insufficient quality
        "vision_only",         # audio failed or no voice input, no adapter
        "independent"          # voice and vision found different components
    ] = Field(..., description="The agreement categorization between modal sensors")
    
    agreement_score:       float = Field(..., ge=0.0, le=1.0, description="Metric of synergy between the voice and vision findings")
    reconciled_components: list[str] = Field(default_factory=list, description="Components correctly identified by both modalities")
    conflict_components:   list[str] = Field(default_factory=list, description="Components where voice and vision actively disagree")
    dominant_source:       Literal["voice", "vision", "adapter", "equal", "none"] = Field(..., description="Which input carried the highest confidence or detail")
    fusion_notes:          str = Field(..., description="Plain-language summary of how the fusion engine resolved the match")


# ─────────────────────────────────────────────────────────────
# MODEL 4 — ContextBucketEntry
# ─────────────────────────────────────────────────────────────

class ContextBucketEntry(BaseModel):
    """
    A single fused finding ready for digestion into an Anomaly record.
    Each entry maps to one anomaly in the final InspectionOutput.
    Voice and vision evidence attached separately for traceability.
    """
    entry_id:               str = Field(..., description="Unique ID for this finding, e.g. E001")
    component:              str = Field(..., description="The canonical targeted component")
    component_location:     Optional[str] = Field(default=None, description="Where the component sits on the machine")
    condition_summary:      str = Field(..., description="Fused summary of the condition")
    severity_indication:    Literal["Critical", "Moderate", "Low", "Normal"] = Field(..., description="Predicted fusion severity")
    voice_evidence:         Optional[str] = Field(default=None, description="Evidence derived from STT")
    vision_evidence:        Optional[str] = Field(default=None, description="Evidence derived from Vision")
    adapter_evidence:       Optional[str] = Field(default=None, description="Evidence derived from Adapter")
    adapter_severity:       Optional[str] = Field(default=None, description="Severity mapped directly from adapter")
    evidence_backed:        bool = Field(..., description="True if multiple modalities agree on the finding")
    technician_review_flag: bool = Field(..., description="True if a conflict exists needing manual intervention")
    source_perceptors:      list[Literal["voice", "vision", "adapter"]] = Field(default_factory=list, description="Which sensors spawned this entry")
    confidence_score:       float = Field(..., ge=0.0, le=1.0, description="Composite final confidence in the finding")
    is_global_safety_override: bool = Field(default=False, description="True when entry originates from Global Safety Clause")
    global_override_category: Optional[str] = Field(default=None, description="Which global safety category triggered this entry")


# ─────────────────────────────────────────────────────────────
# MODEL 5 — CanonicalInspectionContext (ROOT)
# ─────────────────────────────────────────────────────────────

class CanonicalInspectionContext(BaseModel):
    """
    The universal handoff contract between AI inference and all
    downstream consumers. Self-contained. UI-agnostic.
    """
    # ── Identifiers ──
    context_id:          str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID — unique per inspection run")
    session_id:          Optional[str] = Field(default=None, description="Groups multi-image processing jobs")
    created_at:          str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO 8601 timestamp")
    schema_version:      str = Field(default="1.0.0", description="Schema spec adherence version")

    # ── Asset & Run Metadata ──
    asset_id:            str = Field(default="CAT D6N Dozer", description="Equipment being inspected")
    component_category:  str = Field(..., description="Subsystem group being hit")
    inspection_type:     Literal["daily_walkaround", "safety", "TA1", "custom"] = Field(..., description="Type of standard being executed")
    image_filename:      Optional[str] = Field(default=None, description="Source image file loaded")
    subsection_used:     Optional[str] = Field(default=None, description="Prompt injected to Claude")

    # ── Perceptor Outputs ──
    voice_context:       Optional[NormalizedVoiceContext] = Field(default=None, description="Validated Whisper data structure")
    vision_context:      Optional[NormalizedVisionContext] = Field(default=None, description="Validated Claude vision structure")
    adapter_context:     Optional[NormalizedAdapterContext] = Field(default=None, description="Validated Mistral adapter structure")
    adapter_version:     Optional[str] = Field(default=None, description="Mistral Lora Checkpoint version")

    # ── Fusion Layer ──
    fusion_result:       FusionResult = Field(..., description="Orchestration outcomes between the perceptions")

    # ── Fused Findings ──
    context_entries:     list[ContextBucketEntry] = Field(default_factory=list, description="Resolved unified findings for digest")

    # ── Preliminary Assessment ──
    preliminary_status:  Literal["STOP", "CAUTION", "GO", "INSUFFICIENT_DATA"] = Field(..., description="AI estimated safety flag")
    critical_entry_count: int = Field(..., description="Quantity of CRITICAL entries")
    moderate_entry_count: int = Field(..., description="Quantity of MODERATE entries")
    requires_technician_review: bool = Field(..., description="True if any entries carry the tech review flag")

    # ── AI Overview ──
    ai_overview:         str = Field(..., description="Plain english deterministic combination of findings")
    ai_priority_action:  str = Field(..., description="Deterministic highest priority recommendation")

    # ── Documentation Readiness ──
    documentation_ready: bool = Field(..., description="True if data is robust enough to form a complete report")
    missing_inputs:      list[str] = Field(default_factory=list, description="Any missing sensory inputs required")
    downstream_hints:    dict = Field(default_factory=dict, description="Hint bucket for dynamic UI rendering")

    # ── Overview Output ──
    ai_overview_text:    Optional[str] = Field(default=None, description="Plain-text technician report from overview_generator.py")
    overview_path:       Optional[str] = Field(default=None, description="Path to the _overview.txt file on disk")

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent)

    def to_dict(self) -> dict:
        return self.model_dump()
