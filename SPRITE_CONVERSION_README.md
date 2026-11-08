# Capri → Jill Stingray Sprite Conversion Pipeline

## Quick Start

### 1. Install ComfyUI + Required Models
```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt

# Download models to ComfyUI/models/
# ControlNet:
wget -P models/controlnet https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_openpose.safetensors
wget -P models/controlnet https://huggingface.co/lllyasviel/ControlNet-v1-1/resolve/main/control_v11p_sd15_canny.safetensors

# IP-Adapter:
wget -P models/ipadapter https://huggingface.co/h94/IP-Adapter/resolve/main/models/ip-adapter-plus_sd15.safetensors

# Pixel Art Model (SD1.5):
wget -P models/checkpoints https://huggingface.co/xyron/pixel-art-xl/resolve/main/pixel-art-xl.safetensors

# Jill Stingray LoRA (train your own or find on Civitai):
# Place at models/loras/jill-stingray-v1.safetensors
```

### 2. Prepare Reference Image
Place a clean, front-facing Jill Stingray reference image at:
```
G:/capri-desktop/jill_reference.png
```
- **Size:** 512×512 or 1024×1024
- **Style:** Clean line art or high-quality anime screenshot
- **Pose:** Neutral, facing camera, good lighting

### 3. Start ComfyUI with API enabled
```bash
cd ComfyUI
python main.py --listen --enable-cors-api --port 8188
```

### 4. Run Batch Processing
```bash
cd G:/capri-desktop
pip install pillow requests
python batch_jill_sprites.py
```

### 5. Pack Frames into Strips
```bash
python pack_strips.py
```

### 6. Replace Sprites in Capri
```bash
# Backup originals
mv assets/sprites assets/sprites_backup

# Move new sprites
mv assets/sprites_jill_final assets/sprites

# Rebuild Capri (Visual Studio / dotnet build)
# The sprites are embedded as resources at compile time
```

---

## Model Recommendations

| Component | Recommended Model | Why |
|-----------|-------------------|-----|
| Base Checkpoint | `pixel-art-xl` or `revAnimated` | Clean pixel art style |
| LoRA | Train Jill on 20-30 VA-11 Hall-A screenshots | Character consistency |
| ControlNet | OpenPose + Canny | Pose + edge preservation |
| IP-Adapter | `ip-adapter-plus_sd15` | Style transfer from reference |

**LoRA Training Tips:**
- 20-30 high-quality VA-11 Hall-A frames
- Resolution: 512×512, captioned with "jill stingray, VA-11 Hall-A style"
- 10-15 epochs, rank 32, lr 1e-4

---

## Workflow Customization

Edit `comfyui_jill_workflow.json`:
- **Denoise (node 13):** 0.3 = more faithful to original, 0.6 = more creative
- **IP-Adapter weight (node 5):** 0.6-0.9, higher = more Jill-like
- **ControlNet strength (nodes 6,7):** 0.8-1.0, higher = stricter pose adherence

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Reference image not found" | Place `jill_reference.png` in capri-desktop root |
| "Cannot connect to ComfyUI" | Ensure `--listen --enable-cors-api` flags |
| Frames look distorted | Check frame dimensions match (240×384 or 384×384) |
| Inconsistent character | Increase IP-Adapter weight, better reference image, train LoRA |
| Glitch frames too clean | Add "datamosh, heavy corruption" to glitch prompts |

---

## File Structure After Setup
```
G:/capri-desktop/
├── assets/sprites/              # Original Capri sprites (input)
├── sprites_jill/                # Generated frames (intermediate)
├── assets/sprites_jill_final/   # Packed strips (output)
├── jill_reference.png           # Your Jill reference image
├── comfyui_jill_workflow.json   # ComfyUI workflow
├── batch_jill_sprites.py        # Batch processing script
├── pack_strips.py               # Strip packing script
└── SPRITE_CONVERSION_README.md  # This file
```