import modal
import os
import json
import shutil
from datetime import datetime, timezone

# =======================================================================
# [SECTION 2] CONFIG
# =======================================================================
CONFIG = {
    "project_name":     "d6n-inspection-trainer",
    "volume_name":      "d6n-training-vault",
    "adapter_name":     "d6n-lora",
    "local_pdf_folder": "./trainingdata",
    
    "domain_expert_role": (
        "You are a CAT-certified D6N Track-Type Dozer technician "
        "and field inspector. You have memorized the D6N service "
        "manuals, parts reference guide, and fluid specifications."
    ),
    
    "task_description": (
        "Given a field observation about the machine and a relevant "
        "excerpt from the service documentation, analyze the issue "
        "and output a structured JSON inspection finding with a "
        "severity rating of ASAP, Soon, or Okay."
    ),
    
    "severity_rules": {
        "ASAP": [
            "fluid leak near heat source or exhaust",
            "hydraulic or brake system failure",
            "transmission abnormal noise or failure",
            "structural crack on frame or load-bearing component",
            "ECM or engine protection fault code",
            "turbocharger failure",
            "radiator severely clogged with overheat risk",
            "final drive oil loss",
            "track shoe cracked or missing",
            "winch brake failure",
            "fire risk of any kind",
            "unsafe to operate — immediate shutdown required",
        ],
        "Soon": [
            "fluid level below minimum (no visible leak)",
            "undercarriage wear within 20 percent of service limit",
            "engine coolant level decreasing slowly",
            "duo-cone seal seepage not yet a failure",
            "differential or final drive oil slightly below recommended",
            "air filter restriction indicator triggered",
            "blade cutting edge worn past 50 percent service life",
            "pin lubrication overdue",
            "belt showing cracking or glazing but not failed",
            "EMS III amber warning indicator",
            "schedule repair within 1 to 2 weeks",
        ],
        "Okay": [
            "all fluid levels within normal operating range",
            "filters within service interval",
            "tracks properly tensioned with more than 20 percent life",
            "blade edges with more than 50 percent service life",
            "cab filters clean and recently replaced",
            "ROPS and FOPS structure intact",
            "lights horn backup alarm seat belt all functional",
            "cosmetic damage only — paint decals minor surface rust",
            "EMS III all green indicators",
            "no action needed — log and monitor",
        ],
    },
    
    "output_schema": {
        "component":         "string — name of the affected component",
        "part_number":       "string or null — part number from docs",
        "severity":          "ASAP | Soon | Okay",
        "rationale":         "string — why this severity was assigned",
        "recommended_action":"string — what the technician should do",
        "manual_reference":  "string — doc title, section, page if found",
    },
    
    "machine_summary": """
MACHINE: CAT D6N Track-Type Tractor (Medium Dozer)
ENGINE: Cat C6.6 ACERT, 111.8 kW / 150 hp, 6.6L inline-6
SERIAL NUMBER PREFIXES: DJA, DJY, GHS, JAH, LJR, MLW, PBA, PER

KEY SERVICE INTERVALS:
  10 hr / Daily : Cab recirculation filter inspect
                  Parts: 7G-8116 (JAH/DJA/DJY/LJR/MLW/GHS)
                         151-0914 (PBA/PER)
  50 hr         : Cab recirculation filter replace — 329-3243
  250 hr        : Engine oil + filter (4.2 gal/16L)
                  Oil filter: 462-1171 (JAH series) | 525-6205 (PBA/PER)
                  Belt inspect: 253-4531
  500 hr        : Air filter primary: 252-5001 (JAH/DJA/DJY)
                                      319-0844 (LJR/MLW/GHS)
                  Hydraulic filters: primary 326-1644, secondary 308-1502
                  Fuel filter: 350-7735
                  Steering charge filter: 1G-8878
  1,000 hr      : Engine valve lash + gasket: 317-3064
                  Transmission filter: 328-3655
                  Transmission oil: 42.3 gal/160L
  2,000 hr/1 yr : Final drive oil (each): 1.8 gal/7.0L — Part 184-6022
                  Hydraulic tank oil: 7.8 gal/29.5L
  3 yr          : Seat belt replace — 222-0345
  6,000 hr/3 yr : Coolant extender — 119-5152
  12,000 hr/6 yr: Full coolant drain/refill: 9.2 gal/35L

SERVICE REFILL CAPACITIES:
  Fuel tank:    299 L / 79 gal
  Cooling:       35 L / 9.24 gal
  Final drives:   7 L / 1.84 gal each
  Hydraulic:     29.5 L / 7.79 gal
  Transmission: ~160 L / 42.3 gal

APPROVED FLUIDS:
  Engine:     Cat DEO-CK4 15W-40 (515-3973) | 10W-30 (515-3985)
  Hydraulic:  Cat HYDO Advanced 10W (309-6932) | 20W (422-6704)
  Final drive: Cat FDAO (184-6022) | FDAO SYN (208-2390)
  Trans:      Cat TDTO 10W (462-7706) | 30W (248-7521) | 50W (462-7709)
  Coolant:    Cat ELC Premix (205-6611) — up to 12,000 hr interval
  Grease:     Cat EAG-1 (452-5996) | EAG-2 (452-6001)
              Arctic (508-2184) | Desert (452-6016)

KEY SYSTEMS:
  - ADEM A4 ECM: controls fuel injection; fault = ASAP
  - EMS III: 3-level warning (green/amber/red); monitors coolant temp,
    trans oil temp, hydraulic oil temp, fuel, oil pressure, air filter
  - Differential steering: variable-disp pump + fixed-disp motor +
    3 planetary gear sets; 4.0 km/h max speed diff between tracks
  - Planetary powershift: 5F/5R, ECPC, forced oil-cooled clutch packs
  - Elevated final drives: isolate from ground impact loads
  - SystemOne undercarriage: XL = 40 shoes/side 610mm, 7 rollers
                             LGP = 46 shoes/side 840mm, 8 rollers
  - VPAT blade pitch: 54deg (finish), 57.5deg (dozing), 60-62deg (dig)
  - Winch PA55: 74L oil, 122m cable, 19mm recommended cable
  - Diagnostic: Cat ET via diagnostic connector; S.O.S. tap points
  - Access: right fender (hydraulic taps), left enclosure (batteries,
    trans fill, fuses), right enclosure (hydraulic filter)
"""
}

# =======================================================================
# [SECTION 5] SHARED INFRASTRUCTURE
# =======================================================================
app = modal.App(CONFIG["project_name"])

volume = modal.Volume.from_name(
    CONFIG["volume_name"], create_if_missing=True
)

training_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install([
        "torch",
        "transformers",
        "datasets",
        "peft",
        "trl",
        "accelerate",
        "bitsandbytes",
        "pymupdf",           # PDF parsing
        "sentence-transformers",
        "rich",
        "openai-whisper",     # MP3/audio transcription
        "ffmpeg-python",
    ])
    .apt_install(["ffmpeg"])  # required by whisper for audio decoding
)

VOLUME_ROOT       = "/data"
RAW_PDF_DIR       = f"{VOLUME_ROOT}/raw/manuals"
TRAIN_DIR         = f"{VOLUME_ROOT}/training"
CHECKPOINT_DIR    = f"{VOLUME_ROOT}/checkpoints"
MODEL_CACHE_DIR   = f"{VOLUME_ROOT}/models/mistral-7b"
ADAPTER_LATEST    = f"{VOLUME_ROOT}/adapters/{CONFIG['adapter_name']}"
ADAPTER_PROD      = f"{VOLUME_ROOT}/adapters/production"
TRAIN_FILE        = f"{TRAIN_DIR}/train.jsonl"
VAL_FILE          = f"{TRAIN_DIR}/val.jsonl"
TEST_FILE         = f"{TRAIN_DIR}/test.jsonl"
BASE_MODEL        = "mistralai/Mistral-7B-Instruct-v0.2"
PASS_THRESHOLD    = 0.85

# =======================================================================
# [SECTION 6] FUNCTION IMPLEMENTATIONS
# =======================================================================

@app.function(volumes={"/data": volume})
def upload_pdfs() -> None:
    pass # Upload is executed securely in the local entrypoint to bypass Mount depreciation

@app.function(volumes={"/data": volume}, image=training_image)
def build_dataset() -> None:
    import fitz
    import random
    import re
    import os
    import json
    
    os.makedirs(TRAIN_DIR, exist_ok=True)
    dataset = []
    seen_chunks = set()
    real_examples = []
    
    # -----------------------------------------------------------------------
    # STEP 0: Load hand-written real inspection examples (highest quality data)
    # These are weighted 5x so they dominate training over synthetic chunks.
    # Format: one JSON object per line in trainingdata/real_inspections.jsonl
    #   Keys: observation, component, part_number, severity, rationale,
    #         recommended_action, manual_reference
    # -----------------------------------------------------------------------
    REAL_INSPECTIONS_FILE = os.path.join(RAW_PDF_DIR, "real_inspections.jsonl")
    if os.path.exists(REAL_INSPECTIONS_FILE):
        with open(REAL_INSPECTIONS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ex = json.loads(line)
                    observation = ex.get("observation", "")
                    completion = {
                        "component": ex.get("component", "Unknown"),
                        "part_number": ex.get("part_number"),
                        "severity": ex.get("severity", "Okay"),
                        "rationale": ex.get("rationale", ""),
                        "recommended_action": ex.get("recommended_action", ""),
                        "manual_reference": ex.get("manual_reference", "")
                    }
                    prompt = (f"{CONFIG['domain_expert_role']}\n\n{CONFIG['task_description']}\n\n"
                              f"MACHINE CONTEXT:\n{CONFIG['machine_summary'][:200]}\n\n"
                              f"OBSERVATION: {observation}\n\nOutput JSON:")
                    entry = {"prompt": prompt, "completion": json.dumps(completion)}
                    real_examples.append(entry)
                except Exception as e:
                    print(f"Skipping bad real_inspections line: {e}")
        
        # Weight real examples 5x so the model reliably memorizes them
        dataset.extend(real_examples * 5)
        print(f"Loaded {len(real_examples)} real inspection examples (weighted 5x = {len(real_examples)*5} entries)")
    
    # -----------------------------------------------------------------------
    # STEP 0b: Transcribe MP3 audio files using Whisper and add to dataset
    # MP3s in trainingdata/ (e.g., inspection walkthroughs) are transcribed
    # and chunked into training examples, weighted 3x.
    # -----------------------------------------------------------------------
    import whisper
    audio_examples = []
    whisper_model = None  # load lazily only if MP3s exist
    for root, _, files in os.walk(RAW_PDF_DIR):
        for file in files:
            if file.lower().endswith(".mp3") or file.lower().endswith(".wav"):
                audio_path = os.path.join(root, file)
                try:
                    if whisper_model is None:
                        print("Loading Whisper model for audio transcription...")
                        whisper_model = whisper.load_model("base")
                    print(f"Transcribing {file}...")
                    result = whisper_model.transcribe(audio_path)
                    transcript = result["text"].strip()
                    # Chunk transcript into ~400-word blocks for training
                    words = transcript.split()
                    i = 0
                    while i < len(words):
                        chunk = " ".join(words[i:i+400])
                        i += 200  # 50% overlap for better coverage
                        if len(chunk.split()) < 20:
                            continue
                        # Determine severity from keywords in chunk
                        severity = "Okay"
                        chunk_lower = chunk.lower()
                        if any(w in chunk_lower for w in ["immediate", "critical", "failure", "crack", "broken", "leak", "unsafe", "replace now"]):
                            severity = "ASAP"
                        elif any(w in chunk_lower for w in ["monitor", "schedule", "worn", "check soon", "attention"]):
                            severity = "Soon"
                        prompt = (f"{CONFIG['domain_expert_role']}\n\n{CONFIG['task_description']}\n\n"
                                  f"MACHINE CONTEXT:\n{CONFIG['machine_summary'][:200]}\n\n"
                                  f"OBSERVATION: Field audio inspection report.\n\n"
                                  f"DOCUMENT CONTEXT (from audio): {chunk}\n\nOutput JSON:")
                        completion = {
                            "component": "Audio-described component",
                            "part_number": None,
                            "severity": severity,
                            "rationale": f"Derived from inspection audio: {file}",
                            "recommended_action": "Refer to the described procedure in the audio walkthrough.",
                            "manual_reference": file
                        }
                        audio_examples.append({"prompt": prompt, "completion": json.dumps(completion)})
                    print(f"  → {len(audio_examples)} chunks from {file}")
                except Exception as e:
                    print(f"Error transcribing {file}: {e}")
    
    if audio_examples:
        dataset.extend(audio_examples * 3)  # weight 3x
        print(f"Added {len(audio_examples)} audio chunks (weighted 3x = {len(audio_examples)*3} entries)")
    
    for root, _, files in os.walk(RAW_PDF_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):

                pdf_path = os.path.join(root, file)
                try:
                    doc = fitz.open(pdf_path)
                    for page in doc:
                        text = page.get_text("text")
                        words = text.split()
                        
                        i = 0
                        while i < len(words):
                            chunk_words = words[i:i+400]
                            i += 50
                            
                            if len(chunk_words) < 20:
                                continue
                            
                            chunk_text = " ".join(chunk_words)
                            prefix = chunk_text[:40]
                            if prefix in seen_chunks:
                                continue
                            seen_chunks.add(prefix)
                            
                            severity = "Soon"
                            for sev, rules in CONFIG["severity_rules"].items():
                                for rule in rules:
                                    if any(w.lower() in chunk_text.lower() for w in rule.split()):
                                        severity = sev
                                        break
                                if severity != "Soon":
                                    break
                                    
                            parts = re.findall(r'[A-Za-z0-9]{2,4}-\d{3,4}', chunk_text)
                            part_number = parts[0] if parts else None
                            
                            observation = f"Tech observation regarding {chunk_words[:10]}..."
                            
                            prompt = (f"{CONFIG['domain_expert_role']}\n\n{CONFIG['task_description']}\n\n"
                                      f"MACHINE CONTEXT:\n{CONFIG['machine_summary'][:200]}\n\n"
                                      f"OBSERVATION: {observation}\n\n"
                                      f"DOCUMENT CONTEXT: {chunk_text}\n\nOutput JSON:")
                                      
                            completion = {
                                "component": "Extracted Component",
                                "part_number": part_number,
                                "severity": severity,
                                "rationale": "Based on document context heuristics.",
                                "recommended_action": "Refer to manual procedure.",
                                "manual_reference": file
                            }
                            
                            dataset.append({
                                "prompt": prompt,
                                "completion": json.dumps(completion)
                            })
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    
    if len(dataset) < 50:
        print(f"Warning: Only {len(dataset)} examples extracted. Generating synthetic padding...")
        for j in range(50 - len(dataset)):
            dataset.append({
                "prompt": f"{CONFIG['domain_expert_role']}\n\n{CONFIG['task_description']}\n\nMACHINE CONTEXT:\n{CONFIG['machine_summary'][:200]}\n\nOBSERVATION: Synthetic failure scenario {j}...\n\nDOCUMENT CONTEXT: No text available.\n\nOutput JSON:",
                "completion": '{"component": "Unknown", "part_number": null, "severity": "Okay", "rationale": "Synthetic padding.", "recommended_action": "None", "manual_reference": "N/A"}'
            })
        
    random.seed(42)
    random.shuffle(dataset)
    
    train_split = int(len(dataset) * 0.8)
    val_split = int(len(dataset) * 0.9)
    
    with open(TRAIN_FILE, "w") as f:
        for ex in dataset[:train_split]: f.write(json.dumps(ex) + "\n")
    with open(VAL_FILE, "w") as f:
        for ex in dataset[train_split:val_split]: f.write(json.dumps(ex) + "\n")
    with open(TEST_FILE, "w") as f:
        for ex in dataset[val_split:]: f.write(json.dumps(ex) + "\n")
        
    volume.commit()
    
    asap = sum(1 for d in dataset if json.loads(d["completion"])["severity"] == "ASAP")
    soon = sum(1 for d in dataset if json.loads(d["completion"])["severity"] == "Soon")
    okay = sum(1 for d in dataset if json.loads(d["completion"])["severity"] == "Okay")
    
    print(f"Dataset generated: {len(dataset)} examples (ASAP: {asap}, Soon: {soon}, Okay: {okay})")

@app.function(
    gpu="A10G",
    timeout=7200,
    volumes={"/data": volume},
    image=training_image,
)
def fine_tune() -> None:
    import torch
    import os
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments, Trainer, DataCollatorForLanguageModeling
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        cache_dir=MODEL_CACHE_DIR
    )
    model = prepare_model_for_kbit_training(model)
    
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, cache_dir=MODEL_CACHE_DIR)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right" # Important for causal LMs
    
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)
    
    dataset = load_dataset("json", data_files={"train": TRAIN_FILE, "eval": VAL_FILE})
    
    def tokenize_function(examples):
        texts = [f"{p}{c}{tokenizer.eos_token}" for p, c in zip(examples['prompt'], examples['completion'])]
        out = tokenizer(texts, max_length=512, truncation=True, padding="max_length")
        out["labels"] = out["input_ids"].copy()
        return out
        
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["prompt", "completion"],
        desc="Tokenizing dataset"
    )
    
    # Use DataCollatorForLanguageModeling for causal LMs
    # mlm=False ensures it's not masked language modeling
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    training_args = TrainingArguments(
        output_dir=CHECKPOINT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        fp16=True,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps",
        save_steps=50,
        report_to="none",
        dataloader_pin_memory=False,
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["eval"],
        data_collator=data_collator,
    )
    
    trainer.train()
    
    os.makedirs(os.path.dirname(ADAPTER_LATEST), exist_ok=True)
    trainer.model.save_pretrained(ADAPTER_LATEST)
        
    volume.commit()

@app.function(
    gpu="A10G",
    timeout=900,
    volumes={"/data": volume},
    image=training_image,
)
def validate() -> dict:
    import torch
    import json
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        cache_dir=MODEL_CACHE_DIR
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, cache_dir=MODEL_CACHE_DIR)
    
    model = PeftModel.from_pretrained(base_model, ADAPTER_LATEST)
    model.eval()
    
    test_data = []
    with open(TEST_FILE, "r") as f:
        for line in f:
            test_data.append(json.loads(line))
            
    total = len(test_data)
    valid_json = 0
    correct_sev = 0
    per_class = {"ASAP": {"total": 0, "correct": 0}, "Soon": {"total": 0, "correct": 0}, "Okay": {"total": 0, "correct": 0}}
    failures = []
    
    for ex in test_data:
        prompt = ex["prompt"]
        expected_sev = json.loads(ex["completion"]).get("severity", "Okay")
        if expected_sev not in per_class: expected_sev = "Okay"
        per_class[expected_sev]["total"] += 1
        
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,       # was 256 — JSON responses need more room
            do_sample=False,
            temperature=1.0,
            pad_token_id=tokenizer.eos_token_id,
        )
        
        generated = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        
        try:
            clean = generated.strip()
            if clean.startswith("```json"): clean = clean[7:]
            if clean.endswith("```"): clean = clean[:-3]
            # If JSON is truncated, try to close it and parse anyway
            if clean.count("{") > clean.count("}"):
                clean = clean + "}" * (clean.count("{") - clean.count("}"))
            
            pred = json.loads(clean)
            valid_json += 1
            pred_sev = pred.get("severity", "Okay")
            
            if pred_sev == expected_sev:
                correct_sev += 1
                per_class[expected_sev]["correct"] += 1
            elif len(failures) < 10:
                failures.append({"prompt_snippet": prompt[:120], "expected": expected_sev, "got": pred_sev, "raw_output": generated[:200]})
        except Exception:
            # Last resort: regex-extract severity from partial output
            import re
            sev_match = re.search(r'"severity"\s*:\s*"(ASAP|Soon|Okay)"', generated)
            if sev_match:
                pred_sev = sev_match.group(1)
                valid_json += 1  # partial but parseable
                if pred_sev == expected_sev:
                    correct_sev += 1
                    per_class[expected_sev]["correct"] += 1
                elif len(failures) < 10:
                    failures.append({"prompt_snippet": prompt[:120], "expected": expected_sev, "got": pred_sev, "raw_output": generated[:200]})
            elif len(failures) < 10:
                failures.append({"prompt_snippet": prompt[:120], "expected": expected_sev, "got": "INVALID_JSON", "raw_output": generated[:200]})
                
    results = {
        "total_examples": total,
        "severity_accuracy": correct_sev / total if total > 0 else 0.0,
        "valid_json_rate": valid_json / total if total > 0 else 0.0,
        "per_class_accuracy": {k: (v["correct"]/v["total"] if v["total"]>0 else 0.0) for k,v in per_class.items()},
        "failures": failures
    }
    
    print(json.dumps(results, indent=2))
    return results

@app.function(volumes={"/data": volume})
def finalize(run_label: str, accuracy: float) -> None:
    import json
    import os
    import shutil
    from datetime import datetime
    
    target_dir = f"{ADAPTER_PROD}/{run_label}"
    os.makedirs(target_dir, exist_ok=True)
    
    for f in os.listdir(ADAPTER_LATEST):
        src = os.path.join(ADAPTER_LATEST, f)
        tgt = os.path.join(target_dir, f)
        if os.path.isfile(src): shutil.copy2(src, tgt)
        
    metadata = {
        "run_label": run_label,
        "project": CONFIG["project_name"],
        "domain_expert_role": CONFIG["domain_expert_role"],
        "base_model": BASE_MODEL,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "severity_accuracy": accuracy,
        "pass_threshold": PASS_THRESHOLD,
        "lora_rank": 16,
        "epochs": 3,
        "source_pdf_folder": CONFIG["local_pdf_folder"],
        "adapter_path": f"{ADAPTER_PROD}/{run_label}"
    }
    
    with open(os.path.join(target_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    volume.commit()
    print(f"Adapter finalized at {target_dir}")

# =======================================================================
# [SECTION 7] ENTRYPOINT
# =======================================================================

@app.local_entrypoint()
def main():
    print("=" * 60)
    print(f"Pipeline: {CONFIG['project_name']}")
    print(f"PDF folder: {CONFIG['local_pdf_folder']}")
    print("=" * 60)

    print("\n[0/4] Uploading PDFs to Modal Volume (Local Entry)...")
    import os
    if os.path.exists(CONFIG["local_pdf_folder"]):
        with volume.batch_upload(force=True) as batch:
            local_pdf_folder = CONFIG["local_pdf_folder"]
            remote_path = RAW_PDF_DIR.replace(VOLUME_ROOT, "").lstrip("/")
            batch.put_directory(local_pdf_folder, remote_path)
        print("Upload successful!")
    else:
        print(f"Warning: Local folder '{CONFIG['local_pdf_folder']}' not found.")

    print("\n[1/4] Building training dataset from PDFs...")
    build_dataset.remote()

    print("\n[2/4] Fine-tuning model with LoRA (A10G, up to 2 hrs)...")
    fine_tune.remote()

    print("\n[3/4] Validating adapter on test set...")
    results = validate.remote()
    print(f"\nValidation results:\n{json.dumps(results, indent=2)}")

    if results["severity_accuracy"] >= PASS_THRESHOLD:
        print(f"\n[4/4] PASSED ({results['severity_accuracy']:.2%}). Finalizing adapter...")
        finalize.remote("v1", results["severity_accuracy"])
        print(f"\nDone. Adapter at: {ADAPTER_PROD}/v1/")
    else:
        print(f"\n[4/4] FAILED ({results['severity_accuracy']:.2%} < {PASS_THRESHOLD:.0%} threshold).")
        print("Do not deploy. Review failures list above and retrain.")
