#!/bin/bash
# llama-server を nexus-decision-4b (GGUF Q4_K_M + mmproj) で起動する。
# 使い方: ./start_server.sh   (フォアグラウンド。別ターミナルで run_nexus.py を実行)
set -e
cd "$(dirname "$0")"
BIN=./tools/llama-b12441/llama-server
exec "$BIN" \
  -m ./model/nexus-decision-4b.Q4_K_M.gguf \
  --mmproj ./model/nexus-decision-4b.mmproj-Q8_0.gguf \
  --host 127.0.0.1 --port 18080 \
  -c 8192 -t 4 --image-max-tokens 256
