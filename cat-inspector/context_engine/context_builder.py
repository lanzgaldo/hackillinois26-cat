"""
context_engine/context_builder.py
──────────────────────────────────
THE CORE BRAIN of the pipeline.

Responsibility: Given an image and a component category, assemble the
complete context package that gets sent to the inference model. This is
what separates PASS outputs from FAIL outputs:

  FAIL: Wrong subsection prompt loaded → model detects wrong components
        (FailPrompt1 loaded cooling prompt for a steps image)
  FAIL: Missing weight vector → model produces generic JSON without
        confidence scoring (FailPrompt2)
  PASS: Correct subsection + weight vector + schema injected as one
        coherent context → model produces correct, scored JSON

Architecture:
  ContextBuilder
    ├── SubsectionRouter          → selects correct .md prompt file
    ├── WeightCalculator          → resolves weight profile to vector
    ├── SchemaInjector            → appends JSON schema template
    └── assembled ContextPackage  → sent to Modal worker / Vertex
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from context_engine.subsection_router import SubsectionRouter
from context_engine.weight_calculator import WeightCalculator, WeightVector
from schemas.inspection_schema import InspectionOutput


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT PACKAGE — the assembled payload
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ContextPackage:
    """
    Everything the inference model needs, packed into one object.

    Fields:
        system_prompt       — Base expert inspector role (base_inspector.txt)
                              with weight placeholders substituted
        subsection_context  — Component-specific RED/YELLOW/GREEN criteria
        schema_template     — JSON output schema the model must match
        image_b64           — Base64-encoded image bytes
        image_media_type    — e.g. "image/jpeg"
        metadata            — Routing decisions, timestamps, weight profile
        weight_vector       — The resolved weights (injected into system prompt)
    """
    system_prompt:      str
    subsection_context: str
    schema_template:    str
    image_b64:          str
    image_media_type:   str
    weight_vector:      WeightVector
    metadata:           dict = field(default_factory=dict)

    def to_anthropic_messages(self) -> list[dict]:
        """
        Assembles the messages array for Anthropic /v1/messages.
        Layout:
          [system]  base_inspector + weight vector substituted
          [user]    subsection_context + schema_template + image
        """
        user_content = [
            {
                "type": "text",
                "text": self._build_user_text(),
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.image_media_type,
                    "data": self.image_b64,
                },
            },
        ]
        return [{"role": "user", "content": user_content}]

    def _build_user_text(self) -> str:
        return (
            "## COMPONENT INSPECTION CONTEXT\n\n"
            f"{self.subsection_context}\n\n"
            "---\n\n"
            "## REQUIRED OUTPUT SCHEMA\n\n"
            "Populate every field. Do not omit optional fields if evidence exists.\n\n"
            f"{self.schema_template}\n\n"
            "---\n\n"
            "Analyze the provided Caterpillar equipment image now. "
            "Return ONLY the JSON object."
        )

    def to_vertex_request(self) -> dict:
        """
        Formats the package for Vertex AI (Gemini vision) via Antigravity.
        Uses the same context but packaged for Google's API shape.
        """
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"{self.system_prompt}\n\n{self._build_user_text()}"},
                        {
                            "inline_data": {
                                "mime_type": self.image_media_type,
                                "data": self.image_b64,
                            }
                        },
                    ],
                }
            ],
            "generation_config": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "max_output_tokens": 2048,
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

class ContextBuilder:
    """
    Assembles a ContextPackage from raw inputs.

    Usage:
        builder = ContextBuilder()
        package = builder.build(
            image_path="RustOnHydraulicComponentBracket.jpg",
            component_category="hydraulics",
            weight_profile="default",
        )
    """

    PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
    SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system" / "base_inspector.txt"

    def __init__(self):
        self.router    = SubsectionRouter()
        self.weighter  = WeightCalculator()
        self._system   = self.SYSTEM_PROMPT_FILE.read_text()

    # ── public ────────────────────────────────────────────────────────────────

    def build(
        self,
        image_path: str | Path,
        component_category: str,
        weight_profile: str = "default",
        image_bytes: Optional[bytes] = None,
    ) -> ContextPackage:
        """
        Main entry point.

        Args:
            image_path:         Path to the inspection image file
            component_category: One of the keys in SubsectionRouter.ROUTES
            weight_profile:     Named weight profile (see WeightCalculator)
            image_bytes:        If provided, skip disk read (for Modal volume use)
        """
        # 1. Load image
        b64, media_type = self._encode_image(image_path, image_bytes)

        # 2. Resolve weights
        weights = self.weighter.resolve(weight_profile)

        # 3. Build system prompt with weight placeholders substituted
        system = self._inject_weights(self._system, weights)

        # 4. Route to correct subsection prompt
        subsection_path, matched_category = self.router.route(component_category)
        subsection_text = Path(subsection_path).read_text()

        # 5. Build schema template string
        schema_str = self._build_schema_template(weights)

        # 6. Assemble metadata
        meta = {
            "image_path":         str(image_path),
            "component_category": matched_category,
            "weight_profile":     weight_profile,
            "subsection_file":    subsection_path,
            "built_at":           datetime.now(timezone.utc).isoformat(),
        }

        return ContextPackage(
            system_prompt=system,
            subsection_context=subsection_text,
            schema_template=schema_str,
            image_b64=b64,
            image_media_type=media_type,
            weight_vector=weights,
            metadata=meta,
        )

    # ── private ───────────────────────────────────────────────────────────────

    def _encode_image(
        self,
        image_path: str | Path,
        image_bytes: Optional[bytes],
    ) -> tuple[str, str]:
        """Returns (base64_str, media_type)."""
        path = Path(image_path)
        raw = image_bytes or path.read_bytes()
        b64 = base64.b64encode(raw).decode("utf-8")

        ext = path.suffix.lower().lstrip(".")
        MIME = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        media_type = MIME.get(ext, "image/jpeg")
        return b64, media_type

    def _inject_weights(self, system_text: str, weights: WeightVector) -> str:
        """Substitutes {weight_placeholders} in the system prompt."""
        return (
            system_text
            .replace("{visual_clarity_weight}",    str(weights.visual_clarity))
            .replace("{severity_match_weight}",    str(weights.severity_match))
            .replace("{context_alignment_weight}", str(weights.context_alignment))
            .replace("{field_history_weight}",     str(weights.field_history))
        )

    def _build_schema_template(self, weights: WeightVector) -> str:
        """
        Builds the JSON schema string injected into the user message.
        Uses the weight vector so the model sees the actual expected
        weight values when filling in its scores.
        """
        template = {
            "inspection_metadata": {
                "equipment_type": "Caterpillar Heavy Equipment",
                "component_category": "<FILL: matched component category>",
                "inspection_timestamp": "<FILL: ISO 8601 timestamp>",
                "image_filename": "<FILL: filename if known>",
                "model_version": "cat-inspect-v1",
                "subsection_prompt": "<FILL: subsection file used>",
                "weight_profile": "<FILL: weight profile name>",
            },
            "confidence_scoring": {
                "visual_clarity": {
                    "weight": weights.visual_clarity,
                    "score": "<FILL: 0.0–1.0 based on image quality and defect visibility>",
                    "weighted": "<CALCULATED: weight × score>",
                },
                "severity_match": {
                    "weight": weights.severity_match,
                    "score": "<FILL: 0.0–1.0 based on certainty of severity classification>",
                    "weighted": "<CALCULATED: weight × score>",
                },
                "context_alignment": {
                    "weight": weights.context_alignment,
                    "score": "<FILL: 0.0–1.0 based on match with subsection RED/YELLOW/GREEN criteria>",
                    "weighted": "<CALCULATED: weight × score>",
                },
                "field_history": {
                    "weight": weights.field_history,
                    "score": "<FILL: 0.0–1.0 based on match with known CAT field failure patterns>",
                    "weighted": "<CALCULATED: weight × score>",
                },
                "overall_confidence": "<CALCULATED: sum of all weighted values>",
                "confidence_level": "<CALCULATED: High(>=0.90) | Medium(>=0.70) | Low(<0.70)>",
            },
            "anomalies": [
                {
                    "anomaly_id": "A001",
                    "component_location": "<FILL: exact location on machine>",
                    "component_type": "<FILL: CAT component name>",
                    "issue": "<FILL: short issue label>",
                    "condition_description": "<FILL: technical description of observed condition>",
                    "severity": "<FILL: Critical | Moderate | Normal>",
                    "safety_impact_assessment": "<FILL: personnel and operational safety risk>",
                    "visibility_impact": "<FILL: effect on operator visibility>",
                    "operational_impact": "<FILL: effect on equipment operation>",
                    "recommended_action": "<FILL: specific repair or monitoring action>",
                    "anomaly_confidence": "<FILL: 0.0–1.0>",
                    "detection_basis": "<FILL: specific visual evidence observed>",
                }
            ],
            "summary": {
                "critical_count": "<FILL: integer>",
                "moderate_count": "<FILL: integer>",
                "normal_count": "<FILL: integer>",
                "wheel_position": "<FILL: if tire/rim inspection, else null>",
                "operational_status": "<DERIVED: STOP | CAUTION | GO>",
                "priority_action": "<FILL: most urgent single action>",
                "overall_equipment_condition": "<FILL: 1–2 sentence assessment>",
            },
        }
        return json.dumps(template, indent=2)
