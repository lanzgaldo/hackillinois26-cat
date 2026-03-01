import os
import sys
import pytest

# Add paths to enable local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from context_engine.subsection_router import SubsectionRouter
from pipeline.context_bucket import build_context_bucket
from schemas.inspection_schema import InspectionOutput

def test_prompt_verification():
    """Test Case 3: Prompt Verification"""
    router = SubsectionRouter()
    
    # We test a few key known categories to ensure they load properly
    test_categories = ["engine", "hydraulics", "undercarriage"]
    
    for category in test_categories:
        combined_prompt, cat, path = router.load_subsection_prompt(category)
        
        # Verify it appended the global safety clause
        assert "GLOBAL SAFETY OVERRIDE" in combined_prompt
        assert "ALWAYS DETECT AND REPORT" in combined_prompt
        
        # Verify it didn't mutate the underlying category resolution
        assert cat == category
    print("Test Case 3 (Prompt Verification) Passed.")

if __name__ == "__main__":
    print("Running local prompt tests...")
    test_prompt_verification()
    print("Local tests passed. For Test Case 1 & 2 integration tests, run via modal run.")
