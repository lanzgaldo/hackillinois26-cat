"""
schemas/inspection_schema.py
────────────────────────────
Pydantic v2 models defining the EXACT JSON contract that the inference
model must produce. These schemas are derived from the Pass/Fail prompt
analysis:

  PassPrompt1 (Steps):     anomalies[] with component_location, component_type,
                           condition_description, safety_impact_assessment,
                           visibility_impact, operational_impact, recommended_action

  PassPrompt2 (Tires/Rims): anomalies[] with component, issue, description,
                            severity, recommended_action + wheel_position +
                            operational_impact (top-level)

  FailPrompt1: Used wrong subsection context → misidentified components
  FailPrompt2: Partially correct schema but missing critical fields

The unified schema below normalizes both pass formats into one
canonical structure with weighted confidence scoring appended.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class Severity(str, Enum):
    CRITICAL = "Critical"     # RED  — equipment must not operate
    MODERATE = "Moderate"     # YELLOW — schedule maintenance
    NORMAL   = "Normal"       # GREEN — acceptable, continue ops

class OperationalStatus(str, Enum):
    STOP    = "STOP"          # One or more Critical anomalies
    CAUTION = "CAUTION"       # One or more Moderate anomalies, no Critical
    GO      = "GO"            # All Normal
    PENDING_VERIFICATION = "PENDING_VERIFICATION"

class ConfidenceLevel(str, Enum):
    HIGH   = "High"           # 0.90–1.00 — clear visual evidence
    MEDIUM = "Medium"         # 0.70–0.89 — probable, needs verification
    LOW    = "Low"            # 0.50–0.69 — suspicious, closer inspection


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY — core finding unit
# ─────────────────────────────────────────────────────────────────────────────

class Anomaly(BaseModel):
    """
    Unified anomaly record.

    Maps to both PassPrompt formats:
      - PassPrompt1 fields: component_location, component_type,
        condition_description, safety_impact_assessment,
        visibility_impact, operational_impact, recommended_action
      - PassPrompt2 fields: component (→ component_type),
        issue, description (→ condition_description),
        severity, recommended_action
    """
    anomaly_id:               str     = Field(..., description="e.g. A001, A002")
    component_location:       str     = Field(..., description="Specific location on machine, e.g. 'Front Left Rim'")
    component_type:           str     = Field(..., description="e.g. Step, Rim, Hydraulic Hose, Tire")
    issue:                    str     = Field(..., description="Short issue label, e.g. 'Severe Rim Corrosion'")
    condition_description:    str     = Field(..., description="Detailed technical description of observed condition")
    severity:                 Severity
    safety_impact_assessment: str     = Field(..., description="Personnel and operational safety risks")
    visibility_impact:        str     = Field(..., description="Effect on operator visibility and safety awareness")
    operational_impact:       str     = Field(..., description="Effect on equipment operation and mobility")
    recommended_action:       str     = Field(..., description="Specific repair, replacement, or monitoring action")
    anomaly_confidence:       float   = Field(..., ge=0.0, le=1.0,
                                            description="Per-anomaly detection confidence 0.0–1.0")
    detection_basis:          str     = Field(..., description="Visual evidence cited, e.g. 'rust discoloration on rim flange'")

    technician_confirmed: Optional[bool] = Field(
        default=None,
        description=(
            "True = technician confirms AI finding. "
            "False = technician rejects finding, exclude from scoring. "
            "None = not yet reviewed — pipeline in PENDING state."
        )
    )
    technician_severity_override: Optional[Severity] = Field(
        default=None,
        description=(
            "If set, replaces AI severity for this anomaly in final scoring. "
            "Requires technician_override_rationale to be populated. "
            "None = no override, use AI-assigned severity."
        )
    )
    technician_notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description=(
            "Free-text technician observations. "
            "Appended to final report as supporting context. "
            "Does not affect confidence scoring."
        )
    )
    technician_override_rationale: Optional[str] = Field(
        default=None,
        description=(
            "REQUIRED when technician_severity_override is set. "
            "Explains why AI severity was overridden. "
            "Enforced by TechnicianVerification model validator."
        )
    )

    @model_validator(mode="after")
    def enforce_override_rationale(self) -> "Anomaly":
        if self.technician_severity_override is not None:
            if not self.technician_override_rationale or str(self.technician_override_rationale).strip() == "":
                raise ValueError("technician_override_rationale is required when technician_severity_override is set")
        return self


# ─────────────────────────────────────────────────────────────────────────────
# WEIGHT VECTOR — injected by context_engine, scored by inference model
# ─────────────────────────────────────────────────────────────────────────────

class WeightedDimension(BaseModel):
    """One confidence dimension with its pre-set weight and model-assigned score."""
    weight:   float = Field(..., ge=0.0, le=1.0, description="Pre-configured weight (sums to 1.0 across all dimensions)")
    score:    float = Field(..., ge=0.0, le=1.0, description="Model-assigned score for this dimension")
    weighted: float = Field(..., ge=0.0, le=1.0, description="weight × score (calculated)")

    @model_validator(mode="after")
    def enforce_weighted(self) -> "WeightedDimension":
        expected = round(self.weight * self.score, 4)
        self.weighted = expected
        return self


class TechnicianVerification(BaseModel):
    """
    Technician sign-off layer. Injected into InspectionOutput
    after SchemaValidator completes. Pipeline is halted at
    PENDING_VERIFICATION until this model is fully populated.
    """
    technician_id: Optional[str] = Field(
        default=None,
        description="Identifier of reviewing technician. Required before sign-off."
    )
    technician_sign_off: Optional[bool] = Field(
        default=None,
        description=(
            "True = technician approves report. "
            "False = report flagged for supervisor review. "
            "None = awaiting verification."
        )
    )
    verification_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601. System-set when sign-off written. Never accept as input."
    )
    operational_status_override: Optional[OperationalStatus] = Field(
        default=None,
        description=(
            "Technician override of final operational_status. "
            "Cannot override STOP to GO if unreviewed Critical anomalies exist. "
            "None = use SchemaValidator result."
        )
    )
    verification_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Overall technician comments on the inspection report."
    )

    @model_validator(mode="after")
    def enforce_sign_off_requires_id(self) -> "TechnicianVerification":
        if self.technician_sign_off is True:
            if not self.technician_id or str(self.technician_id).strip() == "":
                raise ValueError(
                    "technician_id is required before technician_sign_off can be True"
                )
        return self


class ConfidenceScoring(BaseModel):
    """
    Weighted confidence model.

    Four dimensions (weights must sum to 1.0):
      visual_clarity   — How clearly the defect is visible in the image
      severity_match   — How certain the severity classification is
      context_alignment — How well the finding aligns with the subsection criteria
      field_history    — Match with known CAT field failure patterns
    """
    visual_clarity:    WeightedDimension
    severity_match:    WeightedDimension
    context_alignment: WeightedDimension
    field_history:     WeightedDimension

    overall_confidence: float          = Field(..., ge=0.0, le=1.0)
    confidence_level:   ConfidenceLevel

    @model_validator(mode="after")
    def compute_overall(self) -> "ConfidenceScoring":
        total = (
            self.visual_clarity.weighted
            + self.severity_match.weighted
            + self.context_alignment.weighted
            + self.field_history.weighted
        )
        self.overall_confidence = round(min(total, 1.0), 4)
        if self.overall_confidence >= 0.90:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.overall_confidence >= 0.70:
            self.confidence_level = ConfidenceLevel.MEDIUM
        else:
            self.confidence_level = ConfidenceLevel.LOW
        return self


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY — roll-up
# ─────────────────────────────────────────────────────────────────────────────

class InspectionSummary(BaseModel):
    critical_count:              int
    moderate_count:              int
    normal_count:                int
    wheel_position:              Optional[str] = None  # PassPrompt2 field
    operational_status:          OperationalStatus
    priority_action:             str
    overall_equipment_condition: str

    @model_validator(mode="after")
    def derive_status(self) -> "InspectionSummary":
        if getattr(self, "operational_status", None) == OperationalStatus.PENDING_VERIFICATION:
            return self
        if self.critical_count > 0:
            self.operational_status = OperationalStatus.STOP
        elif self.moderate_count > 0:
            self.operational_status = OperationalStatus.CAUTION
        else:
            self.operational_status = OperationalStatus.GO
        return self


# ─────────────────────────────────────────────────────────────────────────────
# METADATA — inspection run metadata
# ─────────────────────────────────────────────────────────────────────────────

class InspectionMetadata(BaseModel):
    equipment_type:      str = "Caterpillar Heavy Equipment"
    component_category:  str
    inspection_timestamp: str                  # ISO 8601
    image_filename:      Optional[str] = None
    model_version:       str = "cat-inspect-v1"
    subsection_prompt:   str                   # which prompt file was used
    weight_profile:      str = "default"       # named weight profile used


# ─────────────────────────────────────────────────────────────────────────────
# ROOT OUTPUT — the canonical JSON the pipeline produces
# ─────────────────────────────────────────────────────────────────────────────

class InspectionOutput(BaseModel):
    """
    Root object. Fully serializable to JSON.
    This is what gets written to Modal volumes, returned from
    Vertex endpoints, and consumed by downstream systems.
    """
    inspection_metadata: InspectionMetadata
    confidence_scoring:  ConfidenceScoring
    anomalies:           list[Anomaly]
    summary:             InspectionSummary
    technician_verification: Optional[TechnicianVerification] = Field(
        default=None,
        description=(
            "Populated after SchemaValidator completes. "
            "None = verification not yet initiated. "
            "Pipeline halts at PENDING_VERIFICATION until "
            "this is fully populated and signed off."
        )
    )

    def to_json(self, indent: int = 2) -> str:
        return self.model_dump_json(indent=indent, exclude_none=True)

    @model_validator(mode="after")
    def enforce_technician_constraints(self) -> "InspectionOutput":
        # Rule 1: STOP cannot be overridden to GO if any Critical anomaly has technician_confirmed = None or True
        # without a severity override to Moderate or Normal
        if self.technician_verification is not None:
            ov = getattr(self.technician_verification, "operational_status_override", None)
            if ov == OperationalStatus.GO:
                for anomaly in self.anomalies:
                    if anomaly.severity == Severity.CRITICAL:
                        if anomaly.technician_confirmed is None or anomaly.technician_confirmed is True:
                            if anomaly.technician_severity_override not in (Severity.MODERATE, Severity.NORMAL):
                                raise ValueError("Cannot override status to GO with unmitigated Critical anomalies")
        return self

    @classmethod
    def example_pass(cls) -> "InspectionOutput":
        """Mirrors PassPrompt2 structure for unit testing."""
        return cls(
            inspection_metadata=InspectionMetadata(
                component_category="tires_rims",
                inspection_timestamp="2025-02-28T12:00:00Z",
                subsection_prompt="prompts/subsections/tires_rims.md",
            ),
            confidence_scoring=ConfidenceScoring(
                visual_clarity=WeightedDimension(weight=0.35, score=0.95, weighted=0.3325),
                severity_match=WeightedDimension(weight=0.30, score=0.92, weighted=0.276),
                context_alignment=WeightedDimension(weight=0.20, score=0.90, weighted=0.18),
                field_history=WeightedDimension(weight=0.15, score=0.88, weighted=0.132),
                overall_confidence=0.9205,
                confidence_level=ConfidenceLevel.HIGH,
            ),
            anomalies=[
                Anomaly(
                    anomaly_id="A001",
                    component_location="Front Left Rim",
                    component_type="Rim",
                    issue="Severe Rim Corrosion",
                    condition_description="Extensive rust and pitting on rim structure affecting integrity and mounting surfaces.",
                    severity=Severity.CRITICAL,
                    safety_impact_assessment="Critical — structural failure risk and air seal compromise.",
                    visibility_impact="No direct visibility impact.",
                    operational_impact="Wheel separation hazard; equipment must not operate.",
                    recommended_action="Immediate rim replacement.",
                    anomaly_confidence=0.96,
                    detection_basis="Rust discoloration and visible pitting across full rim flange.",
                ),
            ],
            summary=InspectionSummary(
                critical_count=1,
                moderate_count=1,
                normal_count=0,
                wheel_position="Front left",
                operational_status=OperationalStatus.STOP,
                priority_action="Replace corroded rim immediately. Inspect all wheel hardware.",
                overall_equipment_condition="Critical wheel condition. Equipment grounded pending repair.",
            ),
        )
