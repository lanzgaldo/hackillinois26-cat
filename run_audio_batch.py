"""
Batch audio test runner — processes all MP3s in audiotestcases/ through
the full digest_maintenance_event pipeline (Whisper + fine-tuned adapter + Claude)
and saves a combined JSON report.

Usage:
    python -m modal run run_audio_batch.py
"""

import os
import json
import modal

app = modal.App("cat-inspect-audio-batch")

# Reference the already-deployed cat-inspect-ai-sprint1 functions
digest_maintenance_event = modal.Function.from_name("cat-inspect-ai-sprint1", "digest_maintenance_event")

@app.local_entrypoint()
def main():
    audio_dir = "./audiotestcases"
    output_file = "./audiotestcases_results.json"

    mp3_files = sorted([
        f for f in os.listdir(audio_dir)
        if f.lower().endswith(".mp3")
    ])

    print(f"Found {len(mp3_files)} audio files to process.\n")

    results = []

    for i, filename in enumerate(mp3_files):
        filepath = os.path.join(audio_dir, filename)
        print(f"[{i+1}/{len(mp3_files)}] Processing: {filename}")

        with open(filepath, "rb") as f:
            audio_bytes = f.read()

        try:
            result = digest_maintenance_event.remote(audio_bytes, None)
            result["_file"] = filename
            result["_index"] = i + 1
            results.append(result)

            summary   = result.get("inspection_summary", {})
            status    = summary.get("status", "unknown")
            anomalies = result.get("anomalies", [])
            transcript = result.get("raw_transcript", "")[:80]
            adapter_sev = result.get("adapter_classification", {}).get("severity", "N/A")

            print(f"  → Status: {status.upper():<8} | Adapter: {adapter_sev:<5} | Anomalies: {len(anomalies)} | \"{transcript}...\"")

        except Exception as e:
            print(f"  → ERROR: {e}")
            results.append({"_file": filename, "_index": i + 1, "error": str(e)})

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Done. {len(results)} results saved to {output_file}")
    print(f"{'='*60}\n")

    print(f"{'#':<4} {'File':<48} {'Status':<10} {'Adapter':<8} {'Anomalies'}")
    print("-" * 82)
    for r in results:
        if "error" in r:
            print(f"{r['_index']:<4} {r['_file']:<48} ERROR")
        else:
            summary   = r.get("inspection_summary", {})
            status    = summary.get("status", "?")
            adapter   = r.get("adapter_classification", {}).get("severity", "N/A")
            anomalies = len(r.get("anomalies", []))
            print(f"{r['_index']:<4} {r['_file']:<48} {status:<10} {adapter:<8} {anomalies}")




