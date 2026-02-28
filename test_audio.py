import os
import json
import argparse
from modal_app import digest_maintenance_event

def main():
    parser = argparse.ArgumentParser(description="Test CAT Inspect multimodal endpoint.")
    parser.add_argument("--audio", type=str, help="Path to the audio .wav file", default="sample.wav")
    parser.add_argument("--image", type=str, help="Path to the image .jpg file (optional)", default="sample.jpg")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio):
        print(f"Error: Audio file '{args.audio}' not found. Please provide a valid --audio path.")
        return

    with open(args.audio, "rb") as f:
        audio_bytes = f.read()

    image_bytes = None
    if args.image and os.path.exists(args.image):
        with open(args.image, "rb") as f:
            image_bytes = f.read()
            print(f"Loaded image: {args.image} ({len(image_bytes)} bytes)")
    else:
        print("No image provided or image not found. Running in audio-only mode.")

    print("Submitting digest_maintenance_event task to Modal...")
    # call the remote endpoint using Modal's remote invocation syntax
    result = digest_maintenance_event.remote(audio_bytes, image_bytes)
    
    print("\n========================================")
    print("FINAL JSON RESULT")
    print("========================================")
    print(json.dumps(result, indent=2))
    
if __name__ == "__main__":
    main()
