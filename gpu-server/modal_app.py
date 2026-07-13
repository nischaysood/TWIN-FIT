"""
TwinFit — IDM-VTON on Modal (serverless GPU fallback engine).

One-time setup (on your Mac):
    pip install modal
    modal setup                      # opens browser to authenticate
    modal deploy gpu-server/modal_app.py

Deploy prints a URL like:
    https://<you>--twinfit-idm-vton-ui.modal.run

Then in backend/.env:
    TRYON_HF_SPACE=https://<you>--twinfit-idm-vton-ui.modal.run
    TRYON_ENGINE_LABEL=IDM-VTON @ Modal (serverless GPU)

Notes:
- First deploy builds the image (~30-40 min: detectron2 compile + ~15GB weights
  baked in). After that, cold starts are just model-load (~2-3 min).
- GPU: L40S (48GB) is a safe fit. Costs ~$2/hr ONLY while a request keeps a
  container warm; scaledown_window kills it after 5 idle minutes.
"""
import modal

app = modal.App("twinfit-idm-vton")

image = (
    modal.Image.from_registry("pytorch/pytorch:2.1.2-cuda12.1-cudnn8-devel")
    # stop apt from asking interactive questions (tzdata freezes the build otherwise)
    .env({"DEBIAN_FRONTEND": "noninteractive", "TZ": "Etc/UTC"})
    .apt_install("git", "wget", "libgl1", "libglib2.0-0", "build-essential", "ninja-build")
    .run_commands(
        "git clone https://github.com/yisol/IDM-VTON.git /idm",
        # repo has environment.yaml, not requirements.txt — install the known-good
        # dependency set (battle-tested during the hackathon deployment)
        "pip install accelerate==0.25.0 transformers==4.36.2 diffusers==0.25.0 "
        "einops==0.7.0 torchmetrics tqdm scipy opencv-python-headless fvcore "
        "cloudpickle omegaconf pycocotools onnxruntime matplotlib scikit-image av "
        "'huggingface_hub==0.24.7' 'pydantic==2.10.6' 'numpy<2'",
        "pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git'",
        "pip install gradio==4.44.1",
        # preprocessing checkpoints
        "mkdir -p /idm/ckpt/densepose /idm/ckpt/humanparsing /idm/ckpt/openpose/ckpts",
        "wget -q -O /idm/ckpt/densepose/model_final_162be9.pkl "
        "https://dl.fbaipublicfiles.com/densepose/densepose_rcnn_R_50_FPN_s1x/165712039/model_final_162be9.pkl",
        "python -c \"from huggingface_hub import hf_hub_download; import shutil; "
        "files=['ckpt/humanparsing/parsing_atr.onnx','ckpt/humanparsing/parsing_lip.onnx','ckpt/openpose/ckpts/body_pose_model.pth']; "
        "[shutil.copy(hf_hub_download(repo_id='yisol/IDM-VTON', repo_type='space', filename=f), '/idm/'+f) for f in files]\"",
        # bake the ~15GB diffusion weights into the image (fast cold starts)
        "python -c \"from huggingface_hub import snapshot_download; snapshot_download('yisol/IDM-VTON')\"",
        # gradio must bind to 0.0.0.0 for Modal's proxy
        "sed -i \"s/image_blocks.launch()/image_blocks.launch(server_name='0.0.0.0', server_port=7860)/\" /idm/gradio_demo/app.py",
        # gradio 4.44 breaks with FastAPI>=0.116 (TemplateResponse API change)
        "pip install 'fastapi==0.115.6' 'starlette==0.41.3'",
    )
)


@app.function(
    image=image,
    gpu="A10G",             # 24GB — fits IDM-VTON fp16; no payment card required
    timeout=1800,
    scaledown_window=300,   # shut down after 5 idle minutes (saves credits)
)
@modal.web_server(7860, startup_timeout=900)
def ui():
    import os
    import subprocess
    # Modal routes egress through a proxy; gradio's startup self-check must
    # bypass it for localhost or it aborts with "localhost is not accessible".
    env = os.environ.copy()
    env["NO_PROXY"] = env["no_proxy"] = "localhost,127.0.0.1,0.0.0.0"
    # Launch from the repo ROOT — app.py imports 'src.*' relative to it
    # (the exact bug we debugged on the AMD notebook, immortalized here)
    subprocess.Popen("cd /idm && python gradio_demo/app.py", shell=True, env=env)
