import json
import math
from pathlib import Path

import pydantic
import pytest

BASE_DIR = Path(__file__).parent

from context_engine.schema_validator import SchemaValidator
from context_engine.subsection_router import SubsectionRouter, AutoDetectRequired
from context_engine.weight_calculator import WeightCalculator
from schemas.inspection_schema import InspectionOutput


class TestSchemaContracts:
    def test_pass_steps_json_matches_schema(self):
        with open(BASE_DIR / "expected/pass_steps.json") as f:
            data = json.load(f)
        output = InspectionOutput.model_validate(data)
        assert output.summary.critical_count == 0
        assert output.summary.moderate_count == 0
        assert output.summary.operational_status == "GO"

    def test_pass_rims_json_matches_schema(self):
        with open(BASE_DIR / "expected/pass_rims.json") as f:
            data = json.load(f)
        output = InspectionOutput.model_validate(data)
        assert output.summary.critical_count == 1
        assert output.summary.operational_status == "STOP"

    def test_weight_profiles_sum_to_one(self):
        wc = WeightCalculator()
        profiles = wc.list_profiles()
        for name, values in profiles.items():
            total = sum(values.values())
            assert math.isclose(total, 1.0, abs_tol=0.001)

    def test_anomaly_ids_sequential(self):
        for filepath in [BASE_DIR / "expected/pass_steps.json", BASE_DIR / "expected/pass_rims.json"]:
            with open(filepath) as f:
                data = json.load(f)
            
            anomalies = data.get("anomalies", [])
            for i, anomaly in enumerate(anomalies):
                expected_id = f"A{i+1:03d}"
                assert anomaly["anomaly_id"] == expected_id


class TestSubsectionRouter:
    def test_exact_routes(self):
        router = SubsectionRouter()
        from context_engine.subsection_router import ROUTES
        for key in ROUTES:
            if key == "auto":
                continue
            path, category = router.route(key)
            expected_path = str(router.BASE_DIR / ROUTES[key])
            assert path == expected_path
            assert category == key

    def test_fuzzy_routing(self):
        router = SubsectionRouter()
        path, category = router.route("tire wear")
        assert category == "tires_rims"

    def test_auto_raises(self):
        router = SubsectionRouter()
        with pytest.raises(AutoDetectRequired):
            router.route("auto")

    def test_regression_no_cooling_for_steps(self):
        router = SubsectionRouter()
        path, category = router.route("steps_access")
        assert "cooling.md" not in path


class TestSchemaValidator:
    def test_json_extraction_strips_fences(self):
        validator = SchemaValidator()
        raw_text = "```json\n{\"test\": 123}\n```"
        errors = []
        extracted = validator._extract_json(raw_text, errors)
        assert extracted == {"test": 123}

    def test_weighted_recalculated(self):
        validator = SchemaValidator()
        from context_engine.weight_calculator import WeightVector
        
        weight_vec = WeightVector(
            visual_clarity=0.5,
            severity_match=0.5,
            context_alignment=0.0,
            field_history=0.0
        )
        
        data = {
            "inspection_metadata": {
                "component_category": "tires_rims",
                "inspection_timestamp": "2025-02-28T12:00:00Z",
                "subsection_prompt": "prompt.md",
                "weight_profile": "default"
            },
            "confidence_scoring": {
                "visual_clarity": {"weight": 0.5, "score": 0.8, "weighted": 9.9},
                "severity_match": {"weight": 0.5, "score": 0.8, "weighted": 9.9},
                "context_alignment": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "field_history": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "overall_confidence": 0.8,
                "confidence_level": "Medium"
            },
            "anomalies": [],
            "summary": {
                "critical_count": 0,
                "moderate_count": 0,
                "normal_count": 0,
                "operational_status": "GO",
                "priority_action": "None",
                "overall_equipment_condition": "Good"
            }
        }
        
        result = validator.validate(json.dumps(data), weight_vec)
        assert result.success is True
        # Verify it auto-corrected 0.5 * 0.8 = 0.4000
        assert result.output.confidence_scoring.visual_clarity.weighted == 0.4000

    def test_operational_status_stop_on_critical(self):
        validator = SchemaValidator()
        from context_engine.weight_calculator import WeightVector
        
        weight_vec = WeightVector(
            visual_clarity=0.5,
            severity_match=0.5,
            context_alignment=0.0,
            field_history=0.0
        )
        
        data = {
            "inspection_metadata": {
                "component_category": "tires_rims",
                "inspection_timestamp": "2025-02-28T12:00:00Z",
                "subsection_prompt": "prompt.md",
                "weight_profile": "default"
            },
            "confidence_scoring": {
                "visual_clarity": {"weight": 0.5, "score": 0.8, "weighted": 0.4},
                "severity_match": {"weight": 0.5, "score": 0.8, "weighted": 0.4},
                "context_alignment": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "field_history": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "overall_confidence": 0.8,
                "confidence_level": "Medium"
            },
            "anomalies": [
                {
                    "anomaly_id": "A001",
                    "component_location": "Front left Rim",
                    "component_type": "Rim",
                    "issue": "Severe Rim Corrosion",
                    "condition_description": "Extensive rust and pitting observed on the rim structure",
                    "severity": "Critical",
                    "safety_impact_assessment": "Critical",
                    "visibility_impact": "",
                    "operational_impact": "Compromised safety",
                    "recommended_action": "Immediate replacement",
                    "anomaly_confidence": 0.0,
                    "detection_basis": ""
                }
            ],
            "summary": {
                "critical_count": 1,
                "moderate_count": 0,
                "normal_count": 0,
                "operational_status": "GO",
                "priority_action": "None",
                "overall_equipment_condition": "Good"
            }
        }
        
        result = validator.validate(json.dumps(data), weight_vec)
        assert result.success is True
        assert result.output.summary.operational_status.value == "STOP"

    def test_operational_status_go_all_normal(self):
        validator = SchemaValidator()
        from context_engine.weight_calculator import WeightVector
        
        weight_vec = WeightVector(
            visual_clarity=0.5,
            severity_match=0.5,
            context_alignment=0.0,
            field_history=0.0
        )
        
        data = {
            "inspection_metadata": {
                "component_category": "tires_rims",
                "inspection_timestamp": "2025-02-28T12:00:00Z",
                "subsection_prompt": "prompt.md",
                "weight_profile": "default"
            },
            "confidence_scoring": {
                "visual_clarity": {"weight": 0.5, "score": 0.8, "weighted": 0.4},
                "severity_match": {"weight": 0.5, "score": 0.8, "weighted": 0.4},
                "context_alignment": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "field_history": {"weight": 0.0, "score": 0.0, "weighted": 0.0},
                "overall_confidence": 0.8,
                "confidence_level": "Medium"
            },
            "anomalies": [],
            "summary": {
                "critical_count": 0,
                "moderate_count": 0,
                "normal_count": 0,
                "operational_status": "STOP",
                "priority_action": "None",
                "overall_equipment_condition": "Good"
            }
        }
        
        result = validator.validate(json.dumps(data), weight_vec)
        assert result.success is True
        assert result.output.summary.operational_status.value == "GO"


@pytest.mark.skip(reason="requires modal deploy")
class TestModalIntegration:
    def test_inspect_image_tires_rims(self):
        import modal
        inspect_image = modal.Function.from_name("cat-equipment-inspector", "inspect_image")
        result = inspect_image.remote(
            image_path="tests/fixtures/BrokenRimBolt1.jpg",
            component_category="tires_rims",
            weight_profile="default"
        )
        assert result["success"] == True
        InspectionOutput.model_validate(result["output_json"])
        
    def test_inspect_image_steps_access(self):
        import modal
        inspect_image = modal.Function.from_name("cat-equipment-inspector", "inspect_image")
        result = inspect_image.remote(
            image_path="tests/fixtures/GoodStep.jpg",
            component_category="steps_access",
            weight_profile="default"
        )
        assert result["success"] == True
        InspectionOutput.model_validate(result["output_json"])
        
    def test_batch_inspect_parallel(self):
        import json
        import modal
        
        with open(BASE_DIR / "training_manifest.json") as f:
            manifest = json.load(f)
            
        jobs = []
        for example in manifest["training_examples"]:
            jobs.append({
                "image_path": f"tests/fixtures/{example['image_file']}",
                "component_category": example["component_category"],
                "weight_profile": example["weight_profile"]
            })
            
        batch_inspect = modal.Function.from_name("cat-equipment-inspector", "batch_inspect")
        results = batch_inspect.remote(jobs)
        
        assert len(results) == 12
        for result in results:
            assert result["success"] == True
            InspectionOutput.model_validate(result["output_json"])

class TestAdapterIntegration:
    def test_normalize_adapter_critical_mapping(self):
        from pipeline.perceptor_normalizer import normalize_adapter
        raw = {"severity": "ASAP", "component": "Hydraulics", "rationale": "Leaking deeply", "source": "mistral-7b"}
        normalized = normalize_adapter(raw)
        assert normalized is not None
        assert normalized.mapped_severity == "Critical"
        assert normalized.anomalous_condition == "Leaking deeply"
    
    def test_normalize_adapter_missing_returns_none(self):
        from pipeline.perceptor_normalizer import normalize_adapter
        assert normalize_adapter(None) is None
        unknown_map = normalize_adapter({"severity": "Unknown_junk", "something": 1})
        assert unknown_map is not None
        assert unknown_map.mapped_severity == "Unknown"
        
    def test_three_way_fusion_adapter_override(self):
        from pipeline.fusion_engine import run_fusion
        from schemas.context_schema import NormalizedVoiceContext, NormalizedAdapterContext
        
        voice = NormalizedVoiceContext(
            raw_transcript="Everything looks fine",
            detected_components=["Engine"],
            detected_conditions=[],
            inferred_severity="Normal",
            language_confidence=0.9,
            word_count=3,
            technician_sentiment="routine"
        )
        
        adapter = NormalizedAdapterContext(
            raw_prediction="Adapter caught fire flag",
            mapped_severity="Critical",
            confidence=0.95,
            source_model="mistral-test",
            anomalous_condition="fire flag"
        )
        
        fusion, entries = run_fusion(voice, None, adapter)
        assert len(entries) > 0
        assert any(e.severity_indication == "Critical" for e in entries)
        
    def test_schema_validator_enforces_adapter_stop(self):
        validator = SchemaValidator()
        from schemas.context_schema import NormalizedAdapterContext
        from schemas.inspection_schema import InspectionOutput
        
        adapter = NormalizedAdapterContext(
            raw_prediction="", mapped_severity="Critical", confidence=0.9, source_model="test", anomalous_condition="broken test"
        )
        
        data = {
            "inspection_metadata": {"component_category": "auto", "inspection_timestamp": "2023-01-01T00:00:00Z", "subsection_prompt": "x", "weight_profile": "default"},
            "confidence_scoring": {"visual_clarity": {"weight": 0.5, "score": 0.8, "weighted": 0.4}, "severity_match": {"weight": 0.5, "score": 0.8, "weighted": 0.4}, "context_alignment": {"weight": 0.0, "score": 0.0, "weighted": 0.0}, "field_history": {"weight": 0.0, "score": 0.0, "weighted": 0.0}, "overall_confidence": 0.8, "confidence_level": "Medium"},
            "anomalies": [],
            "summary": {"critical_count": 0, "moderate_count": 0, "normal_count": 0, "operational_status": "GO", "priority_action": "None", "overall_equipment_condition": "Good"}
        }
        
        output = InspectionOutput.model_validate(data)
        out2 = validator.enforce_adapter_stop_on_asap(output, adapter)
        assert out2.summary.operational_status.value == "STOP"
        assert "ADAPTER OVERRIDE" in out2.summary.priority_action
