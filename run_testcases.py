import subprocess
import os
import shutil

# Target files requested by user
targets = [
    "CoolingSystemHose.jpg",
    "DamagedAccessLadder.jpg",
    "BrokenRimBolt1.jpg", 
    "BrokenRimBolt2.jpg"
]

def run_tests():
    for t in targets:
        path = f"cat-inspector/uploads/{t}"
        if not os.path.exists(path):
            print(f"File not found: {path} - Skipping")
            continue
            
        print(f"\n--- Testing {t} ---")
        cmd = [
            "python", "-m", "modal", "run", "modal_app.py", 
            "--image-path", path
        ]
        
        try:
            # Run Modal inference
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, 
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            
            # Find the output JSON file in standard output
            output_lines = result.stdout.split('\n')
            json_file = None
            for line in output_lines:
                if line.startswith("[context_bucket] Wrote context JSON to "):
                    # Extra handling based on recent Modal behavior:
                    # sometimes it prints /outputs/UUID, sometimes output/UUID
                    json_file = line.split(" ")[-1].strip()
                    break
                    
            if not json_file:
                print(f"Could not find JSON output signature for {t}")
                continue
                
            # Copy down the json from modal
            uuid_fname = os.path.basename(json_file)
            print(f"Downloading {uuid_fname} from Modal Volume...")
            dl_cmd = [
                "modal", "volume", "get", "cat-inspector-outputs", 
                uuid_fname, f"output/{uuid_fname}"
            ]
            subprocess.run(dl_cmd, check=True)
            
            # Rename it to the requested format (e.g. BrokenRimBolt1.json)
            src_path = f"output/{uuid_fname}"
            name_base = t.split('.')[0]
            dst_path = f"output/{name_base}.json"
            
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                print(f"SUCCESS: Saved payload as output/{name_base}.json")
            else:
                print(f"Failed to copy locally: {src_path}")
                
        except Exception as e:
            print(f"Error testing {t}: {e}")

if __name__ == "__main__":
    run_tests()
