"""
context_engine/weight_calculator.py
─────────────────────────────────────
Manages confidence weight profiles.

A WeightVector has four dimensions that must sum to 1.0:
  visual_clarity    — image quality / defect visibility
  severity_match    — certainty of severity classification
  context_alignment — alignment with subsection RED/YELLOW/GREEN criteria
  field_history     — match with known CAT field failure patterns

Named profiles let you tune behavior per use case:
  "default"    — balanced, general inspection
  "safety"     — up-weights severity for safety-critical reviews
  "audit"      — up-weights context_alignment for compliance audits
  "field"      — up-weights field_history for experienced-inspector mode
  "low_light"  — down-weights visual_clarity for poor image conditions
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightVector:
    visual_clarity:    float  # image quality / defect visible
    severity_match:    float  # confidence in severity call
    context_alignment: float  # match with subsection criteria
    field_history:     float  # match with CAT field failure patterns

    def __post_init__(self):
        total = round(
            self.visual_clarity
            + self.severity_match
            + self.context_alignment
            + self.field_history,
            6
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"WeightVector dimensions must sum to 1.0, got {total}"
            )

    def as_dict(self) -> dict[str, float]:
        return {
            "visual_clarity":    self.visual_clarity,
            "severity_match":    self.severity_match,
            "context_alignment": self.context_alignment,
            "field_history":     self.field_history,
        }


# ─────────────────────────────────────────────────────────────────────────────
# NAMED WEIGHT PROFILES
# ─────────────────────────────────────────────────────────────────────────────

PROFILES: dict[str, WeightVector] = {
    "default": WeightVector(
        visual_clarity=0.35,
        severity_match=0.30,
        context_alignment=0.20,
        field_history=0.15,
    ),
    "safety": WeightVector(
        # Safety reviews penalize ambiguous severity calls
        visual_clarity=0.25,
        severity_match=0.45,
        context_alignment=0.20,
        field_history=0.10,
    ),
    "audit": WeightVector(
        # Compliance audits care most about subsection criteria alignment
        visual_clarity=0.20,
        severity_match=0.25,
        context_alignment=0.40,
        field_history=0.15,
    ),
    "field": WeightVector(
        # Field technicians trust pattern-matching over image quality
        visual_clarity=0.20,
        severity_match=0.25,
        context_alignment=0.20,
        field_history=0.35,
    ),
    "low_light": WeightVector(
        # Poor image conditions — reduce visual_clarity weight, rely more on context
        visual_clarity=0.15,
        severity_match=0.30,
        context_alignment=0.35,
        field_history=0.20,
    ),
}


class WeightCalculator:
    """
    Resolves a named profile string → WeightVector.
    Also supports ad-hoc custom vectors.
    """

    def resolve(self, profile_name: str) -> WeightVector:
        """
        Returns a WeightVector for the given named profile.
        Raises KeyError if the profile doesn't exist.
        """
        if profile_name not in PROFILES:
            raise KeyError(
                f"Unknown weight profile '{profile_name}'. "
                f"Available: {list(PROFILES.keys())}"
            )
        return PROFILES[profile_name]

    def custom(
        self,
        visual_clarity: float,
        severity_match: float,
        context_alignment: float,
        field_history: float,
    ) -> WeightVector:
        """Creates and validates a custom weight vector."""
        return WeightVector(
            visual_clarity=visual_clarity,
            severity_match=severity_match,
            context_alignment=context_alignment,
            field_history=field_history,
        )

    def list_profiles(self) -> dict[str, dict]:
        return {name: vec.as_dict() for name, vec in PROFILES.items()}
