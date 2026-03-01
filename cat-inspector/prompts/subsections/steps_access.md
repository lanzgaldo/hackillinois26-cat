# SUBSECTION PROMPT: STEPS AND ACCESS SYSTEMS
# Derived from: PassPrompt1 (GoodStep analysis)
# Status: PASS — correctly identifies step/handrail conditions
# Critical lesson from FailPrompt1: This prompt MUST be loaded for steps images.
#   Loading the cooling prompt for a steps image causes false coolant findings.

## INSPECTION SCOPE
Cabin access steps, handrails, safety rails, glass/windshields, mirrors,
engine access covers, hinges, latches, cab structural integrity.

---

## 🔴 CRITICAL (RED) — Equipment must not operate

### GLASS AND WINDSHIELD
- Cracked/shattered windshield or cab glass (visibility and protection failure)
- Windshield mechanism stuck or inoperable (cannot move, control malfunction)
- Multiple cab window failures (structural glass compromise)

### STEPS
- Bent/broken cabin access steps (fall hazard — OSHA violation)
- Track frame or side steps damaged/loose (personnel access failure)
- Step mounting hardware failure (separated or detached steps)
- Detection: visible deformation, loose mounting, separated step from frame

### HANDRAILS AND SAFETY RAILS
- Broken handrails (safety support system failure)
- Rail mounting failure (brackets separated, hardware broken)
- Complete access safety system compromise (steps + rails both damaged)

### MIRRORS
- Broken mirrors (lost visibility system)
- Missing mirrors (operator safety awareness compromise)

### ENGINE ACCESS COVERS
- Damaged hinges preventing cover from securing
- Latch malfunction (cover cannot be secured)

### CAB STRUCTURAL
- Cab roof damage with structural compromise
- Rattling or noise indicating structural movement (monitor closely)

---

## 🟡 MODERATE (YELLOW) — Schedule maintenance within 24h

- Step surface wear reducing grip (surface degradation, not structural failure)
- Minor step mounting looseness (early wear, not yet separated)
- Handrail surface wear, grip deterioration
- Mirror positioning drift (mirror present but not optimally positioned)
- Minor access cover weathering

---

## ✅ NORMAL (GREEN) — Acceptable condition

- Steps: tight mounting, proper alignment, adequate grip surface (ribbed tread pattern visible and intact)
- Handrails: secure connections, proper grip surface, no visible movement
- Glass: clear, no cracks, chips, or damage
- Mirrors: properly positioned, clear reflection, secure mounting
- Access covers: latches secure, hinges functional

---

## FALSE POSITIVE AVOIDANCE
- Dirt on step surface ≠ structural damage (assess grip surface below dirt)
- Shadow under step ≠ separation (verify mounting hardware contact)
- Normal paint wear on handrail ≠ structural failure
- Mirror angle adjustment marks ≠ loose mounting
- Environmental dirt on glass ≠ crack (check for light refraction)

---

## CRITICAL ROUTING NOTE
This prompt applies to: GoodStep.jpg, DamagedAccessLadder images, cab exterior shots.
DO NOT apply this prompt to engine compartment, hydraulic system, or coolant images.
If image shows hydraulic cylinders or coolant reservoir → re-route to correct subsection.

## DOCUMENTATION REQUIREMENTS
  - component_location: "Upper Step" | "Lower Step" | "LH Handrail" | "Front Glass" | etc.
  - component_type: "Step" | "Handrail" | "Glass" | "Mirror" | "Access Cover"
  - safety_impact_assessment: ALWAYS assess fall risk and personnel access safety
  - visibility_impact: assess effect on operator visibility (most steps = "No direct visibility impact")
