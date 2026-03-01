"""
antigravity/pipeline.py
────────────────────────
Antigravity (Google AI Studio / Vertex AI) orchestration layer.

Two modes:
  1. STANDALONE  — Full pipeline running entirely on Vertex (Gemini vision)
  2. HYBRID      — Modal handles inference, Antigravity handles orchestration,
                   routing decisions, result aggregation, and BigQuery storage

Antigravity is Google's AI-native development framework that sits on top of
Vertex AI and provides:
  - Agent orchestration
  - Tool/function calling integration
  - Streaming responses
  - Built-in evaluation metrics
  - Direct IDE integration (VS Code extension: "Antigravity by Google")

Architecture in HYBRID mode:
  ┌────────────────────┐     HTTP     ┌───────────────────┐
  │  Antigravity Agent │ ──────────► │  Modal Worker API  │
  │  (Vertex-hosted)   │ ◄────────── │  (inspect_image)   │
  └────────────┬───────┘             └───────────────────┘
               │
          JSON output
               │
     ┌─────────▼──────────┐
     │  BigQuery / Firestore│  (persistent inspection history)
     └──────────────────────┘
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Optional
import requests

# Google Cloud / Vertex imports
# pip install google-cloud-aiplatform google-generativeai
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, Image
    from google.cloud import bigquery
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

from context_engine.context_builder import ContextBuilder
from context_engine.schema_validator import SchemaValidator
from context_engine.weight_calculator import WeightCalculator


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AntigravityConfig:
    """
    All configuration needed to run the Antigravity pipeline.

    Set via environment variables or pass directly.
    """
    # Google Cloud
    gcp_project:      str = os.getenv("GCP_PROJECT", "your-gcp-project")
    gcp_region:       str = os.getenv("GCP_REGION",  "us-central1")
    gcp_bucket:       str = os.getenv("GCP_BUCKET",  "cat-inspector-images")
    bq_dataset:       str = os.getenv("BQ_DATASET",  "cat_inspections")
    bq_table:         str = os.getenv("BQ_TABLE",    "inspection_results")

    # Modal
    modal_endpoint:   str = os.getenv("MODAL_ENDPOINT", "https://your-workspace--cat-equipment-inspector-inspect-image.modal.run")
    modal_token:      str = os.getenv("MODAL_TOKEN", "")

    # Vertex / Gemini
    vertex_model:     str = os.getenv("VERTEX_MODEL", "gemini-1.5-pro-vision")

    # Pipeline behavior
    use_modal_inference: bool = True   # False = use Vertex directly
    write_to_bigquery:   bool = True
    max_retries:         int  = 3


# ─────────────────────────────────────────────────────────────────────────────
# ANTIGRAVITY PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

class AntigravityPipeline:
    """
    Main orchestration pipeline.

    Usage (hybrid mode — Modal does inference, Antigravity orchestrates):
        pipeline = AntigravityPipeline(config)
        result = pipeline.run(
            image_path="gs://cat-inspector-images/BrokenRimBolt1.jpg",
            component_category="tires_rims",
            weight_profile="safety",
        )

    Usage (standalone mode — Vertex/Gemini does inference):
        config.use_modal_inference = False
        result = pipeline.run(...)
    """

    def __init__(self, config: Optional[AntigravityConfig] = None):
        self.config    = config or AntigravityConfig()
        self.builder   = ContextBuilder()
        self.validator = SchemaValidator()
        self.weighter  = WeightCalculator()

        if VERTEX_AVAILABLE and not self.config.use_modal_inference:
            vertexai.init(
                project=self.config.gcp_project,
                location=self.config.gcp_region,
            )

    def run(
        self,
        image_path: str,
        component_category: str = "auto",
        weight_profile: str = "default",
        image_bytes: Optional[bytes] = None,
    ) -> dict:
        """
        Main pipeline entry point.

        Returns the final validated inspection JSON dict.
        """
        start = time.time()

        if self.config.use_modal_inference:
            result = self._run_via_modal(image_path, component_category, weight_profile, image_bytes)
        else:
            result = self._run_via_vertex(image_path, component_category, weight_profile, image_bytes)

        result["pipeline_latency_ms"] = int((time.time() - start) * 1000)

        if self.config.write_to_bigquery and VERTEX_AVAILABLE and result.get("success"):
            self._write_to_bigquery(result)

        return result

    # ── Modal inference path ──────────────────────────────────────────────────

    def _run_via_modal(
        self,
        image_path: str,
        component_category: str,
        weight_profile: str,
        image_bytes: Optional[bytes],
    ) -> dict:
        """
        POSTs to the Modal web endpoint.
        Modal worker handles ContextBuilder, Claude API call, and validation.
        """
        payload = {
            "image_path":         image_path,
            "component_category": component_category,
            "weight_profile":     weight_profile,
        }
        if image_bytes:
            import base64
            payload["image_bytes_b64"] = base64.b64encode(image_bytes).decode()

        for attempt in range(self.config.max_retries):
            try:
                resp = requests.post(
                    self.config.modal_endpoint,
                    json=payload,
                    headers={"Authorization": f"Bearer {self.config.modal_token}"},
                    timeout=90,
                )
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    return {"success": False, "error": str(e)}
                time.sleep(2 ** attempt)

    # ── Vertex / Gemini inference path ────────────────────────────────────────

    def _run_via_vertex(
        self,
        image_path: str,
        component_category: str,
        weight_profile: str,
        image_bytes: Optional[bytes],
    ) -> dict:
        """
        Runs the full context build + Gemini inference directly on Vertex.
        Used when Modal is not available or cost optimization requires it.
        """
        if not VERTEX_AVAILABLE:
            return {"success": False, "error": "google-cloud-aiplatform not installed"}

        weights = self.weighter.resolve(weight_profile)
        package = self.builder.build(
            image_path=image_path,
            component_category=component_category,
            weight_profile=weight_profile,
            image_bytes=image_bytes,
        )

        # Build Gemini request from context package
        vertex_req = package.to_vertex_request()
        model = GenerativeModel(self.config.vertex_model)

        response = model.generate_content(
            vertex_req["contents"],
            generation_config=vertex_req["generation_config"],
        )
        raw_text = response.text

        result = self.validator.validate(raw_text, weights)
        return {
            "success":    result.success,
            "output_json": result.output.model_dump() if result.output else None,
            "errors":     result.errors,
            "corrections": result.corrections,
        }

    # ── BigQuery persistence ──────────────────────────────────────────────────

    def _write_to_bigquery(self, result: dict) -> None:
        """
        Writes inspection result to BigQuery for historical trending,
        compliance audit trail, and Looker Studio dashboards.

        BQ Schema (auto-created on first write):
          inspection_id, timestamp, image_path, component_category,
          weight_profile, overall_confidence, confidence_level,
          operational_status, critical_count, moderate_count,
          normal_count, full_json
        """
        try:
            bq = bigquery.Client(project=self.config.gcp_project)
            table_ref = f"{self.config.gcp_project}.{self.config.bq_dataset}.{self.config.bq_table}"

            output = result.get("output_json", {})
            meta   = output.get("inspection_metadata", {})
            conf   = output.get("confidence_scoring", {})
            summ   = output.get("summary", {})

            row = {
                "inspection_id":      meta.get("inspection_timestamp", ""),
                "timestamp":          meta.get("inspection_timestamp"),
                "image_path":         meta.get("image_filename", ""),
                "component_category": meta.get("component_category", ""),
                "weight_profile":     meta.get("weight_profile", ""),
                "overall_confidence": conf.get("overall_confidence", 0.0),
                "confidence_level":   conf.get("confidence_level", ""),
                "operational_status": summ.get("operational_status", ""),
                "critical_count":     summ.get("critical_count", 0),
                "moderate_count":     summ.get("moderate_count", 0),
                "normal_count":       summ.get("normal_count", 0),
                "full_json":          json.dumps(output),
            }

            errors = bq.insert_rows_json(table_ref, [row])
            if errors:
                print(f"[antigravity] BQ insert errors: {errors}")

        except Exception as e:
            print(f"[antigravity] BQ write failed (non-fatal): {e}")
