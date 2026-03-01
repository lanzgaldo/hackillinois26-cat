"""
scripts/deploy.py
──────────────────
Deployment script for Modal AI + Antigravity setup.

Run once to:
  1. Validate all subsection prompt files exist
  2. Verify Pydantic schema imports work
  3. Deploy Modal worker
  4. Print Antigravity IDE setup instructions

Usage:
  python scripts/deploy.py [--dry-run] [--modal-only] [--validate-only]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def validate_prompts() -> bool:
    print("\n[1/4] Validating subsection prompts...")
    REQUIRED = [
        "prompts/system/base_inspector.txt",
        "prompts/subsections/tires_rims.md",
        "prompts/subsections/steps_access.md",
        "prompts/subsections/cooling.md",
        "prompts/subsections/hydraulics.md",
        "prompts/subsections/structural.md",
        "prompts/subsections/engine.md",
        "prompts/subsections/undercarriage.md",
    ]
    all_ok = True
    for f in REQUIRED:
        path = ROOT / f
        if path.exists():
            print(f"  ✅  {f}")
        else:
            print(f"  ❌  MISSING: {f}")
            all_ok = False
    return all_ok


def validate_schema() -> bool:
    print("\n[2/4] Validating Pydantic schemas...")
    try:
        sys.path.insert(0, str(ROOT))
        from schemas.inspection_schema import InspectionOutput
        example = InspectionOutput.example_pass()
        print(f"  ✅  InspectionOutput schema valid")
        print(f"  ✅  Example PASS output: confidence={example.confidence_scoring.overall_confidence}")
        return True
    except Exception as e:
        print(f"  ❌  Schema validation failed: {e}")
        return False


def validate_weights() -> bool:
    print("\n[3/4] Validating weight profiles...")
    try:
        from context_engine.weight_calculator import WeightCalculator
        wc = WeightCalculator()
        for name, vec in wc.list_profiles().items():
            total = sum(vec.values())
            status = "✅" if abs(total - 1.0) < 0.001 else "❌"
            print(f"  {status}  {name}: sum={total:.4f} | {vec}")
        return True
    except Exception as e:
        print(f"  ❌  Weight validation failed: {e}")
        return False


def deploy_modal(dry_run: bool = False) -> bool:
    print("\n[4/4] Deploying Modal worker...")
    if dry_run:
        print("  ⏭️  DRY RUN — skipping modal deploy")
        print("  Run: modal deploy modal_app/worker.py")
        return True
    try:
        result = subprocess.run(
            ["modal", "deploy", "modal_app/worker.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print(f"  ✅  Modal deploy successful")
            print(result.stdout)
            return True
        else:
            print(f"  ❌  Modal deploy failed:\n{result.stderr}")
            return False
    except FileNotFoundError:
        print("  ❌  'modal' CLI not found. Install: pip install modal && modal setup")
        return False


def print_antigravity_setup():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║           ANTIGRAVITY IDE SETUP (Google AI Studio)               ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  1. Install VS Code extension: "Antigravity by Google"            ║
║     (search in Extensions marketplace)                           ║
║                                                                   ║
║  2. Open this project folder in VS Code                           ║
║     Antigravity will auto-detect antigravity/antigravity.yaml    ║
║                                                                   ║
║  3. Set secrets in Antigravity sidebar:                           ║
║     • ANTHROPIC_API_KEY                                           ║
║     • MODAL_TOKEN (from modal token new)                          ║
║     • GCP_PROJECT (your Google Cloud project ID)                  ║
║                                                                   ║
║  4. In Antigravity IDE:                                           ║
║     • Pipeline graph auto-renders from antigravity.yaml           ║
║     • Prompt editor opens prompts/ files with live diff           ║
║     • Weight slider panel adjusts profiles in real-time           ║
║     • Run evaluations: Antigravity > Run Evals                    ║
║                                                                   ║
║  5. To test against Pass/Fail examples:                           ║
║     Antigravity > Evaluations > pass_fail_alignment               ║
║     This runs all fixtures and shows PASS/FAIL per image          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def main():
    parser = argparse.ArgumentParser(description="CAT Inspector deployment")
    parser.add_argument("--dry-run",       action="store_true")
    parser.add_argument("--modal-only",    action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    checks = []
    checks.append(validate_prompts())
    checks.append(validate_schema())
    checks.append(validate_weights())

    if not args.validate_only:
        checks.append(deploy_modal(dry_run=args.dry_run))

    print_antigravity_setup()

    if all(checks):
        print("\n✅  All checks passed. System ready.")
        sys.exit(0)
    else:
        print("\n❌  Some checks failed. Review output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
