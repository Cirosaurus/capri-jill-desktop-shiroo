#!/usr/bin/env python3
"""
Pack processed Jill frames back into horizontal strips matching Capri's expected format.
"""

from pathlib import Path
from PIL import Image

OUTPUT_ROOT = Path(__file__).parent / "sprites_jill"
FINAL_ROOT = Path(__file__).parent / "assets" / "sprites_jill_final"

ANIMATIONS = {
    "idle": (16, 240, 384),
    "blink": (4, 240, 384),
    "blink_glitch": (4, 240, 384),
    "grin": (16, 240, 384),
    "glitch": (10, 240, 384),
    "dangle": (24, 240, 384),
    "sleep": (16, 240, 384),
    "wake": (13, 240, 384),
    "perch": (16, 384, 384),
    "perch_blink": (4, 384, 384),
    "perch_blink_glitch": (4, 384, 384),
    "perch_glitch": (10, 384, 384),
    "mouth": (5, 240, 384),
}

def pack_animation(anim_name, frames, frame_width, frame_height):
    input_dir = OUTPUT_ROOT / anim_name
    output_dir = FINAL_ROOT
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all generated frames (ComfyUI saves with timestamp prefix)
    frame_files = sorted(input_dir.glob(f"jill_{anim_name}_*.png"))

    if len(frame_files) != frames:
        print(f"  ⚠ {anim_name}: expected {frames} frames, found {len(frame_files)}")
        return False

    # Create horizontal strip
    strip_width = frames * frame_width
    strip = Image.new("RGBA", (strip_width, frame_height), (0, 0, 0, 0))

    for i, frame_file in enumerate(frame_files):
        frame = Image.open(frame_file)
        # Resize if needed
        if frame.size != (frame_width, frame_height):
            frame = frame.resize((frame_width, frame_height), Image.LANCZOS)
        strip.paste(frame, (i * frame_width, 0))

    output_file = output_dir / f"{anim_name}.png"
    strip.save(output_file)
    print(f"  ✅ {anim_name}.png → {strip_width}×{frame_height} ({frames} frames)")
    return True

def main():
    print(f"📦 Packing strips from {OUTPUT_ROOT} → {FINAL_ROOT}")

    success = 0
    for anim_name, (frames, width, height) in ANIMATIONS.items():
        if pack_animation(anim_name, frames, width, height):
            success += 1

    print(f"\n{'='*50}")
    print(f"Packed: {success}/{len(ANIMATIONS)} animations")
    print(f"Final sprites in: {FINAL_ROOT}")
    print("\nTo use in Capri:")
    print(f"  1. Backup original: rename assets/sprites → assets/sprites_backup")
    print(f"  2. Move final: mv assets/sprites_jill_final assets/sprites")
    print(f"  3. Rebuild Capri (embeds sprites as resources)")

if __name__ == "__main__":
    main()