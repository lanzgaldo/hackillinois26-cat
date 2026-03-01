# SUBSECTION PROMPT: COOLING SYSTEM
# Context: Coolant reservoir, radiator, hoses, water pump, temperature systems
# FailPrompt2 lesson: "Limited reservoir visibility" is NOT a valid finding.
#   Only report it if visibility prevents ALL assessment, not as a standalone anomaly.

## INSPECTION SCOPE
Coolant reservoir, radiator core + guards, cooling hoses + clamps,
water pump, coolant level indicators, radiator doors.

## 🔴 CRITICAL
- Coolant level BELOW minimum mark on reservoir/radiator (engine overheating risk)
- Active coolant leak: pooling, streaming, dried trails on components
- Radiator core damage / guard missing (core exposed to impact)
- Water pump leakage at inspection hole
- Milky coolant = water-in-oil contamination (ENGINE OIL CONTAINS WATER = Critical)
- Cooling hose blown or clamped failed (pressure loss)
- Radiator door bent/broken (cooling system exposure)

## 🟡 MODERATE
- Coolant approaching service interval (discoloration, degraded appearance)
- Radiator fins bent/debris-blocked (reduced airflow, not total failure)
- Hose clamps showing early loosening (no active leak yet)
- Minor hose surface cracking (not through-wall, no leak)

## ✅ NORMAL
- Coolant between MIN and MAX marks, clean color (green/orange = normal, NOT milky)
- No visible leaks, all components dry
- Radiator clean, guards intact, doors functional
- Hoses properly routed, clamps tight

## FALSE POSITIVES
- Water condensation ≠ coolant leak (check color and location)
- Normal coolant color change with age ≠ contamination
- Coolant expansion/contraction ≠ level problem (check cold vs. hot spec)
- Previous maintenance residue ≠ active leak

## DOCUMENTATION NOTE
If reservoir level IS NOT VISIBLE due to image angle → state "Level not assessable from
this angle" in condition_description but DO NOT create a standalone anomaly for it.
Assess all other visible components and note the limitation in the summary.
