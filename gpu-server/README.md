# TwinFit GPU Server — IDM-VTON on AMD MI300X

This folder runs on your **AMD Developer Cloud** GPU instance, not your Mac.
It serves real IDM-VTON virtual try-on over HTTP for the TwinFit backend.

## 1. Get an AMD GPU instance

Sign in at [AMD Developer Cloud](https://www.amd.com/en/developer/resources/cloud-access/amd-developer-cloud.html) (hackathon credits apply), create a **1× MI300X** droplet with the **PyTorch + ROCm** image, and note its public IP.

## 2. Set up (on the instance)

```bash
# copy this folder to the instance first:
#   scp -r gpu-server root@<AMD_IP>:~/
ssh root@<AMD_IP>
cd ~/gpu-server
bash setup_amd.sh          # installs ROCm PyTorch, clones IDM-VTON, downloads checkpoints
```

## 3. Run

```bash
bash start.sh              # gradio demo on :7860 + JSON bridge on :9000
```

First launch downloads ~15GB of diffusion weights from HuggingFace — give it a few minutes. Open the firewall for port 9000 (or SSH-tunnel: `ssh -L 9000:localhost:9000 root@<AMD_IP>`).

## 4. Point TwinFit at it (on your Mac)

In `backend/.env`:

```dotenv
IDM_VTON_URL=http://<AMD_IP>:9000
```

Restart the backend. Try-on jobs now run IDM-VTON on the MI300X first and fall back to FLUX Kontext (Fireworks) only if the GPU server is unreachable.

## Test directly

```bash
curl http://<AMD_IP>:9000/health
# → {"status":"ok","engine":"IDM-VTON","gpu":"AMD MI300X (ROCm)"}
```

## Notes

- IDM-VTON's code uses `cuda` device names — ROCm PyTorch exposes AMD GPUs through the same API, so it runs unmodified.
- `detectron2` (DensePose) compiles from source against the ROCm torch; if the build fails, install ninja (`pip install ninja`) and retry.
- The bridge auto-masks the upper body. Bottoms/dresses would need the mask category changed in the gradio demo (`get_mask_location('hd', "upper_body", ...)`).
