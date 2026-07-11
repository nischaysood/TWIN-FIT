#!/usr/bin/env bash
# Start IDM-VTON gradio demo (:7860) + TwinFit bridge (:9000) on the AMD instance.
set -e
source ~/vton-env/bin/activate

cd ~/IDM-VTON/gradio_demo
nohup python app.py > ~/gradio.log 2>&1 &
echo "IDM-VTON gradio starting on :7860 (first run downloads ~15GB of weights — watch ~/gradio.log)"

# Wait for gradio to come up (weights load can take several minutes)
until curl -s http://127.0.0.1:7860 > /dev/null; do
  echo "waiting for gradio..."; sleep 10
done

cd "$(dirname "$0")"
echo "Starting bridge on :9000"
uvicorn bridge:app --host 0.0.0.0 --port 9000
