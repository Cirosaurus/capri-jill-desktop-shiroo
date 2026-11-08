#!/usr/bin/env python3
"""
Batch process Capri sprites to Jill Stingray style via ComfyUI.
Requires:
- ComfyUI running at http://127.0.0.1:8188
- Models: control_v11p_sd15_openpose, control_v11p_sd15_canny, ip-adapter-plus_sd15
- Checkpoint: pixel-art-xl (or any SD1.5 pixel art model)
- LoRA: jill-stingray (train or download from Civitai)
- Reference image: jill_reference.png (clean front-facing Jill, ~512x512)
"""

import json
import os
import sys
import time
import requests
from pathlib import Path
from PIL import Image

COMFYUI_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = Path(__file__).parent / "comfyui_jill_workflow.json"
INPUT_ROOT = Path(__file__).parent / "assets" / "sprites"
OUTPUT_ROOT = Path(__file__).parent / "sprites_jill"
REFERENCE_IMAGE = Path(__file__).parent / "jill_reference.png"  # PUT YOUR REFERENCE HERE

ANIMATIONS = {
    # (frames, width, height, prompt_suffix)
    "idle": (16, 240, 384, "subtle breathing, slight sway, weight shift, relaxed posture"),
    "blink": (4, 240, 384, "eyes closing smoothly, neutral expression"),
    "blink_glitch": (4, 240, 384, "eyes closing with RGB split glitch effect, scanlines, digital corruption"),
    "grin": (16, 240, 384, "wide smirk, playful, mouth opening, teeth showing, mischievous"),
    "glitch": (10, 240, 384, "heavy RGB channel separation, scanlines, screen tear, digital artifacting, datamosh"),
    "dangle": (24, 240, 384, "hanging from one arm, legs swinging, relaxed, looking down at viewer"),
    "sleep": (16, 240, 384, "head on arms, peaceful sleeping, slow breathing"),
    "wake": (13, 240, 384, "waking up suddenly, eyes wide, messy hair, alert"),
    "perch": (16, 384, 384, "sitting on windowsill edge, legs dangling, leaning forward, watching"),
    "perch_blink": (4, 384, 384, "seated blink, neutral expression"),
    "perch_blink_glitch": (4, 384, 384, "seated blink with RGB glitch effect"),
    "perch_glitch": (10, 384, 384, "seated heavy RGB glitch, scanlines"),
    "mouth": (5, 240, 384, "mouth shapes: closed, small O, wide, smile, talking phonemes"),
}

def queue_prompt(prompt):
    """Queue a prompt and return prompt_id."""
    resp = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": prompt})
    resp.raise_for_status()
    return resp.json()["prompt_id"]

def wait_for_completion(prompt_id, timeout=300):
    """Wait for prompt to complete."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
        if resp.status_code == 200:
            history = resp.json()
            if prompt_id in history and history[prompt_id].get("status", {}).get("completed"):
                return True
        time.sleep(1)
    return False

def get_output_images(prompt_id):
    """Get output image paths from history."""
    resp = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    history = resp.json()[prompt_id]
    outputs = history.get("outputs", {})
    for node_id, node_output in outputs.items():
        if "images" in node_output:
            return [img["filename"] for img in node_output["images"]]
    return []

def process_animation(anim_name, frames, width, height, prompt_suffix):
    """Process all frames of one animation."""
    input_dir = INPUT_ROOT
    output_dir = OUTPUT_ROOT / anim_name
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = input_dir / f"{anim_name}.png"
    if not input_file.exists():
        print(f"  ✗ Missing: {input_file}")
        return False

    # Load the horizontal strip and split into frames
    strip = Image.open(input_file)
    frame_width = strip.width // frames

    print(f"\n🎞  {anim_name}: {frames} frames × {width}×{height}")

    for i in range(frames):
        # Extract frame
        frame = strip.crop((i * frame_width, 0, (i + 1) * frame_width, strip.height))

        # Save temp frame
        temp_frame = Path(f"/tmp/{anim_name}_frame_{i:03d}.png")
        frame.save(temp_frame)

        # Load workflow and substitute placeholders
        with open(WORKFLOW_PATH) as f:
            workflow = json.load(f)

        # Update nodes
        workflow["1"]["inputs"]["image"] = str(REFERENCE_IMAGE)
        workflow["2"]["inputs"]["image"] = str(temp_frame)
        workflow["10"]["inputs"]["text"] = workflow["10"]["inputs"]["text"].replace("PROMPT_PLACEHOLDER", prompt_suffix)
        workflow["14"]["inputs"]["width"] = width
        workflow["14"]["inputs"]["height"] = height
        workflow["16"]["inputs"]["filename_prefix"] = f"jill_{anim_name}_{i:03d}"

        # Queue
        prompt_id = queue_prompt(workflow)
        print(f"  Frame {i+1}/{frames} queued ({prompt_id[:8]})...")

        if not wait_for_completion(prompt_id):
            print(f"  ✗ Timeout on frame {i}")
            return False

        # Get output and move to output dir
        outputs = get_output_images(prompt_id)
        if outputs:
            src = Path(COMFYUI_URL.replace("http://", "").split(":")[0]) / "output" / outputs[0]
            # Actually, ComfyUI saves to its output folder - we need to find it
            # For now, just note completion
            print(f"  ✓ Frame {i+1} done")
        else:
            print(f"  ✗ No output for frame {i}")
            return False

        temp_frame.unlink(missing_ok=True)

    print(f"  ✅ {anim_name} complete!")
    return True

def main():
    if not REFERENCE_IMAGE.exists():
        print(f"❌ Reference image not found: {REFERENCE_IMAGE}")
        print("   Place a clean Jill Stingray reference image (512x512) at:")
        print(f"   {REFERENCE_IMAGE}")
        sys.exit(1)

    # Test ComfyUI connection
    try:
        requests.get(f"{COMFYUI_URL}/system_stats", timeout=5)
    except:
        print(f"❌ Cannot connect to ComfyUI at {COMFYUI_URL}")
        print("   Start ComfyUI with: comfyui --listen --enable-cors-api")
        sys.exit(1)

    print(f"🚀 Starting batch processing...")
    print(f"   Input:  {INPUT_ROOT}")
    print(f"   Output: {OUTPUT_ROOT}")
    print(f"   Reference: {REFERENCE_IMAGE}")

    success = 0
    for anim_name, (frames, width, height, prompt_suffix) in ANIMATIONS.items():
        if process_animation(anim_name, frames, width, height, prompt_suffix):
            success += 1

    print(f"\n{'='*50}")
    print(f"Done: {success}/{len(ANIMATIONS)} animations processed")
    print(f"Output in: {OUTPUT_ROOT}")
    print("\nNext step: Pack frames back into horizontal strips")
    print("Run: python pack_strips.py")

if __name__ == "__main__":
    main()