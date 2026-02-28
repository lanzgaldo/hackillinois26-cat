"""
context_engine/subsection_router.py
────────────────────────────────────
Maps a component_category string → the correct subsection prompt file.

This is the PRIMARY fix for FailPrompt1's failure mode:
  ❌ FAIL: Steps image + Cooling System prompt → hallucinated coolant findings
  ✅ PASS: Steps image + Steps & Access prompt → correct step/handrail findings

The router supports:
  1. Exact key matching          ("tires_rims"  → tires_rims.md)
  2. Keyword fuzzy matching      ("tire wear"   → tires_rims.md)
  3. Vision-assisted auto-detect (category="auto" → calls lightweight classifier)
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE TABLE
# Maps canonical category keys → subsection prompt files
# Keys are what SubsectionRouter.route() accepts (case-insensitive)
# ─────────────────────────────────────────────────────────────────────────────

ROUTES: dict[str, str] = {
    # Key                    Subsection prompt file
    "tires_rims":            "prompts/subsections/tires_rims.md",
    "steps_access":          "prompts/subsections/steps_access.md",
    "cooling":               "prompts/subsections/cooling.md",
    "hydraulics":            "prompts/subsections/hydraulics.md",
    "structural":            "prompts/subsections/structural.md",
    "engine":                "prompts/subsections/engine.md",
    "undercarriage":         "prompts/subsections/undercarriage.md",
    "auto":                  None,  # resolved dynamically
}

# Keyword → category mapping for fuzzy matching
KEYWORD_MAP: dict[str, str] = {
    # Tires & Rims
    "tire":         "tires_rims",
    "tyre":         "tires_rims",
    "rim":          "tires_rims",
    "wheel":        "tires_rims",
    "lug":          "tires_rims",
    "bolt":         "tires_rims",
    "tread":        "tires_rims",
    # Steps & Access
    "step":         "steps_access",
    "ladder":       "steps_access",
    "handrail":     "steps_access",
    "rail":         "steps_access",
    "glass":        "steps_access",
    "mirror":       "steps_access",
    "cab":          "steps_access",
    "access":       "steps_access",
    # Cooling
    "coolant":      "cooling",
    "radiator":     "cooling",
    "hose":         "cooling",
    "cooling":      "cooling",
    "water":        "cooling",
    "temperature":  "cooling",
    # Hydraulics
    "hydraulic":    "hydraulics",
    "cylinder":     "hydraulics",
    "seal":         "hydraulics",
    "bracket":      "hydraulics",
    "fitting":      "hydraulics",
    "pump":         "hydraulics",
    # Structural
    "frame":        "structural",
    "crack":        "structural",
    "weld":         "structural",
    "structural":   "structural",
    "deform":       "structural",
    "rops":         "structural",
    # Engine
    "engine":       "engine",
    "filter":       "engine",
    "belt":         "engine",
    "air":          "engine",
    "fuel":         "engine",
    "oil":          "engine",
    # Undercarriage
    "track":        "undercarriage",
    "sprocket":     "undercarriage",
    "idler":        "undercarriage",
    "roller":       "undercarriage",
    "undercarriage":"undercarriage",
    "pin":          "undercarriage",
}


@dataclass
class RouteResult:
    category:        str
    prompt_file:     str
    match_method:    str   # "exact" | "fuzzy" | "auto" | "fallback"
    confidence:      float # routing confidence


class SubsectionRouter:
    """
    Routes an incoming category string to a subsection prompt file.

    Priority order:
      1. Exact key match in ROUTES
      2. Keyword fuzzy match in KEYWORD_MAP
      3. Auto-detect (if category == "auto") — returns special marker
      4. Fallback to "engine" with low confidence
    """

    BASE_DIR = Path(__file__).parent.parent

    def route(self, category: str) -> tuple[str, str]:
        """
        Returns (prompt_file_path, resolved_category).
        Raises ValueError if the resolved prompt file doesn't exist and
        we're not in auto mode.
        """
        result = self._resolve(category)

        if result.match_method == "auto":
            # Caller (ContextBuilder or Modal worker) handles auto-detection
            # by running a lightweight image classifier first
            raise AutoDetectRequired("Component category is 'auto'; run image classifier first.")

        prompt_path = self.BASE_DIR / result.prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Subsection prompt not found: {prompt_path}\n"
                f"Create it or check ROUTES table in subsection_router.py"
            )

        return str(prompt_path), result.category

    def _resolve(self, category: str) -> RouteResult:
        normalized = category.lower().strip()

        # 1. Exact match
        if normalized in ROUTES:
            if normalized == "auto":
                return RouteResult("auto", "", "auto", 1.0)
            return RouteResult(
                category=normalized,
                prompt_file=ROUTES[normalized],
                match_method="exact",
                confidence=1.0,
            )

        # 2. Fuzzy keyword match
        tokens = re.split(r"[\s_\-/]+", normalized)
        for token in tokens:
            if token in KEYWORD_MAP:
                cat = KEYWORD_MAP[token]
                return RouteResult(
                    category=cat,
                    prompt_file=ROUTES[cat],
                    match_method="fuzzy",
                    confidence=0.85,
                )

        # 3. Fallback
        return RouteResult(
            category="engine",
            prompt_file=ROUTES["engine"],
            match_method="fallback",
            confidence=0.40,
        )

    def list_categories(self) -> list[str]:
        return [k for k in ROUTES if k != "auto"]


class AutoDetectRequired(Exception):
    """Raised when category='auto' — caller must run image classifier."""
    pass
