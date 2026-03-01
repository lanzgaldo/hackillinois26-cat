import os
import subprocess
from pathlib import Path

def run_pass_fail_tests():
    pass_dir = Path("Pass")
    fail_dir = Path("Fail")
    
    audio_file = Path("sample.mp3")
    if not audio_file.exists():
        mp3s = list(Path(".").glob("*.mp3"))
        if mp3s:
            audio_file = mp3s[0]
        else:
            print("No mp3 found, tests cannot run")
            return
            
    test_cases = []
    
    if pass_dir.exists():
        for img in pass_dir.glob("*.jpg"):
            test_cases.append({"image": str(img), "type": "PASS"})
            
    if fail_dir.exists():
        for img in fail_dir.glob("*.jpg"):
            test_cases.append({"image": str(img), "type": "FAIL"})
            
    print(f"Discovered {len(test_cases)} test cases in Pass/Fail folders.")
    
    for idx, case in enumerate(test_cases, 1):
        img_path = case["image"]
        case_type = case["type"]
        
        print(f"\n[{idx}/{len(test_cases)}] Executing Test on {img_path} ({case_type})")
        
        category = "auto"
        if "Rim" in img_path:
            category = "tires_rims"
        elif "Ladder" in img_path or "Step" in img_path:
            category = "steps_access"
        elif "Cool" in img_path or "Radiator" in img_path:
            category = "cooling"
            
        cmd = [
            "python", "-X", "utf8", "-m", "modal", "run", "modal_app.py::main", 
            "--audio-path", str(audio_file),
            "--image-path", img_path,
            "--category", category
        ]
        
        print(f"Running: {' '.join(cmd)}")
        try:
            # Capture output to save the JSON
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
            out = result.stdout
            json_start = out.find("--- FINAL JSON RESULT ---")
            
            if json_start != -1:
                json_str = out[json_start + 25:].strip()
                start = json_str.find("{")
                if start != -1:
                    json_str = json_str[start:]
                    
                    # Generate filename e.g. 001_PASS_BrokenRimBolt1.json
                    base_name = Path(img_path).stem
                    num_prefix = f"{idx:03d}"
                    out_name = f"{num_prefix}_{case_type}_{base_name}.json"
                    out_path = Path("output") / out_name
                    
                    # Ensure output dir exists
                    Path("output").mkdir(exist_ok=True)
                    
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(json_str)
                        
                    print(f"Success. Wrote {out_name}")
            else:
                print("Failed to find JSON payload in output.")
        except subprocess.CalledProcessError as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    run_pass_fail_tests()
