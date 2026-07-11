#!/usr/bin/env bash
# ============================================================
# TwinFit — IDM-VTON setup on AMD Developer Cloud (MI300X, ROCm)
# Run this ON the AMD GPU instance (Ubuntu 22.04 + ROCm 6.x image).
# ============================================================
set -e

echo "── 1. System deps ──────────────────────────────────────"
sudo apt-get update
sudo apt-get install -y git python3-venv python3-dev build-essential libgl1 libglib2.0-0

echo "── 2. Python env ───────────────────────────────────────"
python3 -m venv ~/vton-env
source ~/vton-env/bin/activate
pip install --upgrade pip wheel

echo "── 3. PyTorch for ROCm (AMD GPUs) ──────────────────────"
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.2

echo "── 4. Verify the MI300X is visible ─────────────────────"
python3 -c "import torch; assert torch.cuda.is_available(), 'GPU NOT VISIBLE — check ROCm install'; print('GPU:', torch.cuda.get_device_name(0))"

echo "── 5. Clone IDM-VTON ───────────────────────────────────"
cd ~
[ -d IDM-VTON ] || git clone https://github.com/yisol/IDM-VTON.git
cd IDM-VTON

echo "── 6. Python deps ──────────────────────────────────────"
# Repo requirements minus torch (already installed for ROCm)
grep -viE '^(torch|torchvision|torchaudio)' requirements.txt > req_no_torch.txt || cp requirements.txt req_no_torch.txt
pip install -r req_no_torch.txt
# detectron2 (needed for DensePose) — builds against the ROCm torch
pip install 'git+https://github.com/facebookresearch/detectron2.git'
# API + bridge deps
pip install gradio_client fastapi uvicorn httpx huggingface_hub

echo "── 7. Preprocessing checkpoints ────────────────────────"
mkdir -p ckpt/densepose ckpt/humanparsing ckpt/openpose/ckpts
# DensePose (official detectron2 model zoo)
[ -f ckpt/densepose/model_final_162be9.pkl ] || \
  wget -O ckpt/densepose/model_final_162be9.pkl \
  https://dl.fbaipublicfiles.com/densepose/densepose_rcnn_R_50_FPN_s1x/165712039/model_final_162be9.pkl
# Human parsing + OpenPose (from the official HF Space)
python3 - <<'EOF'
from huggingface_hub import hf_hub_download
import shutil
files = {
    "ckpt/humanparsing/parsing_atr.onnx":       "ckpt/humanparsing/parsing_atr.onnx",
    "ckpt/humanparsing/parsing_lip.onnx":       "ckpt/humanparsing/parsing_lip.onnx",
    "ckpt/openpose/ckpts/body_pose_model.pth":  "ckpt/openpose/ckpts/body_pose_model.pth",
}
for remote, local in files.items():
    p = hf_hub_download(repo_id="yisol/IDM-VTON", repo_type="space", filename=remote)
    shutil.copy(p, local)
    print("ok:", local)
EOF

echo "── 8. Done ─────────────────────────────────────────────"
echo "Main diffusion weights (yisol/IDM-VTON, ~15GB) auto-download from"
echo "HuggingFace on first launch."
echo ""
echo "Start everything with:  bash ~/IDM-VTON/../gpu-server/start.sh"
echo "(or see gpu-server/README.md)"
