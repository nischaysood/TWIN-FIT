#!/usr/bin/env bash
# ============================================================
# Serve Gemma 3 27B (vision) on the AMD MI300X with vLLM/ROCm.
# Run ON the AMD instance. Exposes an OpenAI-compatible API on :8001.
#
# Requires: HF_TOKEN env var (Gemma is a gated model — accept the
# license once at https://huggingface.co/google/gemma-3-27b-it)
# ============================================================
set -e

if [ -z "$HF_TOKEN" ]; then
  echo "Set HF_TOKEN first:  export HF_TOKEN=hf_xxx  (free HF account,"
  echo "must have accepted the Gemma license on the model page)"
  exit 1
fi

# AMD's official vLLM image for ROCm — includes all GPU deps
docker run -d --name gemma3 \
  --device=/dev/kfd --device=/dev/dri \
  --group-add video --ipc=host \
  --security-opt seccomp=unconfined \
  -e HF_TOKEN="$HF_TOKEN" \
  -p 8001:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  rocm/vllm:latest \
  vllm serve google/gemma-3-27b-it \
    --dtype bfloat16 \
    --max-model-len 8192 \
    --port 8000

echo ""
echo "Gemma 3 27B is loading on the MI300X (first run downloads ~55GB)."
echo "Watch progress:   docker logs -f gemma3"
echo "Test when ready:  curl http://localhost:8001/v1/models"
echo ""
echo "Then in TwinFit backend/.env on your Mac:"
echo "  GEMMA_BASE_URL=http://<AMD_IP>:8001/v1"
echo "  GEMMA_MODEL=google/gemma-3-27b-it"
