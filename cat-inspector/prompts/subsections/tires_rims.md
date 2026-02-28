# SUBSECTION PROMPT: TIRES AND RIMS
# Derived from: PassPrompt2 (BrokenRimBolt1 + BrokenRimBolt2 analysis)
# Status: PASS — produces correct component identification and severity classification

## INSPECTION SCOPE
Tires, rims, wheel hardware (lug nuts, bolts), valve stems, wheel mounting surfaces.
NOTE: Most CAT tracked vehicles have N/A tires — confirm wheeled equipment before proceeding.

---

## 🔴 CRITICAL (RED) — Equipment must not operate

### TIRE FAILURES
- Flat tires, visible punctures, tread separation, exposed cords/steel belts
- Sidewall bulging, cuts reaching cord layer, blowout evidence

### RIM AND WHEEL HARDWARE FAILURES
- Cracked or broken rim structure (linear fractures, separated sections, oval deformation)
- Missing lug nuts or wheel bolts — WHEEL SEPARATION HAZARD
- Loose wheel hardware (protruding, cross-threaded, or undertorqued fasteners)
- Severe rim corrosion: pitting, flaking metal, holes compromising structural integrity
  → Field pattern: rust discoloration + visible pitting across rim flange = Critical
- Bent rims (oval cross-section visible)

### COMMON FIELD FAILURE PATTERNS (HIGH field_history weight)
- "Severe Rim Corrosion" → extensive rust + pitting on rim structure → Critical
- "Missing Lug Nut" → one or more empty stud holes → Critical
- "Wheel Separation" → combination of corrosion + loose hardware → Critical
- Tire/rim combination failures common after >2000 hours without inspection

---

## 🟡 MODERATE (YELLOW) — Schedule maintenance within 24–48h

- Reduced tread depth (wear indicators visible but cords not exposed)
- Uneven wear patterns (center wear, edge wear) → indicates alignment or pressure issues
- Minor rim damage: small dents, surface scratches, surface rust NOT affecting structure
- Cracked or deteriorated valve stems, missing valve caps
- Weather checking on sidewalls (shallow surface cracks, no cord exposure)
- Pin and bushing wear in wheel mounting

---

## ✅ NORMAL (GREEN) — Acceptable, continue operations

- Adequate tread depth with even wear pattern
- All lug nuts/bolts present, properly torqued, no rust staining
- Rim structurally intact, round profile, clean mounting surfaces
- Proper tire inflation (normal profile, even ground contact patch)
- Normal surface oxidation NOT affecting rim structural integrity
- Clean, clear tread design with no embedded objects

---

## FALSE POSITIVE AVOIDANCE
- Mud/dirt on rim ≠ corrosion damage (clean and re-inspect)
- Normal rim surface patina ≠ structural corrosion (look for pitting depth)
- Lighting shadow in lug nut pocket ≠ missing lug nut (count all positions)
- Standard tire deflection under load ≠ flat tire
- Camera angle distortion ≠ bent rim (verify from multiple angles)

---

## DOCUMENTATION REQUIREMENTS
For each anomaly, always populate:
  - wheel_position: "Front left" | "Front right" | "Rear left" | "Rear right"
  - component: "Rim" | "Tire" | "Wheel Hardware" | "Valve Stem"
  - issue: short label (e.g., "Severe Rim Corrosion", "Missing Lug Nut")
  - All confidence weight dimensions scored
