# CAT Equipment Inspection AI — Modal + Antigravity Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEPLOYMENT TARGETS                           │
│   Modal AI (inference worker)   +   Antigravity / Google AI Studio  │
└───────────────┬────────────────────────────────┬────────────────────┘
                │                                │
                ▼                                ▼
   ┌────────────────────────┐      ┌─────────────────────────┐
   │  modal_app/            │      │  antigravity/           │
   │  ├── worker.py         │      │  ├── pipeline.py        │
   │  ├── image_preprocessor│      │  ├── vertex_caller.py   │
   │  └── volume_store.py   │      │  └── antigravity.yaml   │
   └────────────┬───────────┘      └────────────┬────────────┘
                │                               │
                └──────────────┬────────────────┘
                               ▼
              ┌────────────────────────────────┐
              │       context_engine/          │
              │  ├── context_builder.py        │  ← CORE BRAIN
              │  ├── subsection_router.py      │  ← Routes image → prompt
              │  ├── weight_calculator.py      │  ← Weighted confidence
              │  └── schema_validator.py       │  ← JSON enforcement
              └────────────────────────────────┘
```

## Stack
- **Modal AI**: GPU inference workers, image preprocessing, volume-based prompt storage
- **Antigravity (Google AI Studio / Vertex)**: Orchestration pipeline, model routing, IDE integration
- **Claude claude-sonnet-4-20250514**: Vision model for structured JSON output
- **Python 3.11+** with Pydantic v2 for schema enforcement

## Quick Start
```bash
pip install modal anthropic google-cloud-aiplatform pydantic
modal setup
python scripts/deploy.py
```
