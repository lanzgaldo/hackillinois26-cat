"""
context_engine/schema_validator.py
────────────────────────────────────
Post-processes raw model JSON output and enforces the Pydantic schema.

Two-phase validation:
  Phase 1 — Parse: extract valid JSON from model output (handles edge cases
             where models add markdown fences or preamble despite instructions)
  Phase 2 — Validate: run through Pydantic InspectionOutput schema,
             auto-correct calculable fields (weighted scores, overall_confidence,
             confidence_level, operational_status), flag residual issues.

This is the last line of defense before the output leaves the pipeline.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from schemas.inspection_schema import (
    InspectionOutput,
    ConfidenceScoring,
    WeightedDimension,
    ConfidenceLevel,
    InspectionSummary,
    OperationalStatus,
    Severity,
)
from schemas.context_schema import NormalizedAdapterContext
from context_engine.weight_calculator import WeightVector


@dataclass
class ValidationResult:
    success:       bool
    output:        Optional[InspectionOutput]
    raw_json:      Optional[dict]
    errors:        list[str]
    corrections:   list[str]  # fields that were auto-corrected


class SchemaValidator:
    """
    Parses and validates raw model output against InspectionOutput.
    Auto-corrects derived fields (weighted scores, counts, status).
    """

    def validate(
        self,
        raw_text: str,
        weights: WeightVector,
        adapter_context: Optional[NormalizedAdapterContext] = None,
    ) -> ValidationResult:
        """
        Args:
            raw_text: The raw string response from the inference model
            weights:  The WeightVector used for this inspection (for recalculation)
        """
        errors: list[str] = []
        corrections: list[str] = []

        # ── Phase 1: Extract JSON ─────────────────────────────────────────────
        raw_dict = self._extract_json(raw_text, errors)
        if raw_dict is None:
            return ValidationResult(False, None, None, errors, corrections)

        # ── Phase 2: Auto-correct calculable fields ───────────────────────────
        raw_dict = self._autocorrect(raw_dict, weights, corrections)

        # ── Phase 3: Pydantic parse ───────────────────────────────────────────
        try:
            output = InspectionOutput.model_validate(raw_dict)
            output = self.enforce_global_safety_stops(output)
            output = self.enforce_adapter_stop_on_asap(output, adapter_context)
            output = self.enforce_adapter_conflict_review(output, adapter_context)
            return ValidationResult(True, output, raw_dict, errors, corrections)
        except Exception as e:
            errors.append(f"Pydantic validation failed: {e}")
            return ValidationResult(False, None, raw_dict, errors, corrections)

    # ── Private: JSON extraction ──────────────────────────────────────────────

    def _extract_json(self, text: str, errors: list[str]) -> Optional[dict]:
        """
        Attempts to extract a JSON object from model output.
        Handles: clean JSON, markdown-fenced JSON, JSON with preamble.
        """
        # Strip markdown fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()

        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try extracting first {...} block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                errors.append(f"JSON extraction failed: {e}")
                return None

        errors.append("No JSON object found in model output.")
        return None

    # ── Private: Auto-correction ──────────────────────────────────────────────

    def _autocorrect(
        self,
        d: dict,
        weights: WeightVector,
        corrections: list[str],
    ) -> dict:
        """
        Recalculates all derived fields from raw inputs.
        This ensures consistency even if the model made arithmetic errors.
        """
        d = self._fix_confidence_scoring(d, weights, corrections)
        d = self._fix_anomaly_ids(d, corrections)
        d = self._fix_summary_counts(d, corrections)
        d = self._fix_operational_status(d, corrections)
        return d

    def _fix_confidence_scoring(
        self, d: dict, weights: WeightVector, corrections: list[str]
    ) -> dict:
        cs = d.get("confidence_scoring", {})
        dims = {
            "visual_clarity":    weights.visual_clarity,
            "severity_match":    weights.severity_match,
            "context_alignment": weights.context_alignment,
            "field_history":     weights.field_history,
        }
        total = 0.0
        for dim_key, w in dims.items():
            dim = cs.get(dim_key, {})
            if isinstance(dim, dict):
                score = float(dim.get("score", 0.8))
                score = max(0.0, min(1.0, score))
                weighted = round(w * score, 4)
                if dim.get("weighted") != weighted:
                    corrections.append(f"confidence_scoring.{dim_key}.weighted recalculated")
                cs[dim_key] = {"weight": w, "score": score, "weighted": weighted}
                total += weighted

        overall = round(min(total, 1.0), 4)
        if cs.get("overall_confidence") != overall:
            corrections.append("confidence_scoring.overall_confidence recalculated")
        cs["overall_confidence"] = overall

        level = "High" if overall >= 0.90 else "Medium" if overall >= 0.70 else "Low"
        if cs.get("confidence_level") != level:
            corrections.append("confidence_scoring.confidence_level recalculated")
        cs["confidence_level"] = level

        d["confidence_scoring"] = cs
        return d

    def _fix_anomaly_ids(self, d: dict, corrections: list[str]) -> dict:
        anomalies = d.get("anomalies", [])
        for i, a in enumerate(anomalies):
            expected_id = f"A{i+1:03d}"
            if a.get("anomaly_id") != expected_id:
                a["anomaly_id"] = expected_id
                corrections.append(f"anomaly[{i}].anomaly_id set to {expected_id}")
        return d

    def _fix_summary_counts(self, d: dict, corrections: list[str]) -> dict:
        anomalies = d.get("anomalies", [])
        crit = sum(1 for a in anomalies if a.get("severity") == "Critical")
        mod  = sum(1 for a in anomalies if a.get("severity") == "Moderate")
        norm = sum(1 for a in anomalies if a.get("severity") == "Normal")

        s = d.get("summary", {})
        for key, val in [("critical_count", crit), ("moderate_count", mod), ("normal_count", norm)]:
            if s.get(key) != val:
                corrections.append(f"summary.{key} corrected to {val}")
                s[key] = val
        d["summary"] = s
        return d

    def _fix_operational_status(self, d: dict, corrections: list[str]) -> dict:
        s = d.get("summary", {})
        crit = s.get("critical_count", 0)
        mod  = s.get("moderate_count", 0)

        expected = "STOP" if crit > 0 else "CAUTION" if mod > 0 else "GO"
        if s.get("operational_status") != expected:
            corrections.append(f"summary.operational_status corrected to {expected}")
            s["operational_status"] = expected
        d["summary"] = s
        return d

    def enforce_global_safety_stops(self, output: InspectionOutput) -> InspectionOutput:
        """
        If ANY anomaly has is_global_safety_override == True
        AND severity == Critical:
          → operational_status must be STOP regardless of segment findings
          → This is non-negotiable. A critical global safety hazard
            grounds the equipment even if all segment checks pass.

        Log a warning when this override fires so the UI can surface
        a specific message: "Equipment grounded due to safety hazard
        detected outside active inspection segment."
        """
        has_critical_global = False
        for anomaly in output.anomalies:
            if getattr(anomaly, "is_global_safety_override", False) and anomaly.severity == Severity.CRITICAL:
                has_critical_global = True
                break
        
        if has_critical_global:
            output.summary.operational_status = OperationalStatus.STOP
            print("WARNING: Equipment grounded due to safety hazard detected outside active inspection segment.")
        
        return output

    def enforce_adapter_stop_on_asap(self, output: InspectionOutput, adapter: Optional[NormalizedAdapterContext]) -> InspectionOutput:
        """
        If the adapter (finetuned Mistral) explicitly rated the issue as Critical/ASAP,
        and it wasn't already caught by standard schemas, we force operational_status to STOP
        if it applies to a critical component.
        """
        if adapter and adapter.mapped_severity == "Critical":
            if output.summary.operational_status != OperationalStatus.STOP:
                output.summary.operational_status = OperationalStatus.STOP
                action_pfx = f"ADAPTER OVERRIDE: {adapter.anomalous_condition}. " if adapter.anomalous_condition else "ADAPTER OVERRIDE (CRITICAL). "
                output.summary.priority_action = action_pfx + output.summary.priority_action
                print("WARNING: Equipment grounded due to finetuned adapter override.")
        return output

    def enforce_adapter_conflict_review(self, output: InspectionOutput, adapter: Optional[NormalizedAdapterContext]) -> InspectionOutput:
        """
        If the adapter prediction directly conflicts with the merged summary severity
        (e.g., adapter=Critical but summary=Moderate/Normal), 
        flag the output for manual technician review.
        """
        if adapter and adapter.mapped_severity == "Critical" and output.summary.critical_count == 0:
            output.summary.operational_status = OperationalStatus.PENDING_VERIFICATION
            print("WARNING: Conflict triggered. Adapter designated Critical but findings did not match.")
        return output

