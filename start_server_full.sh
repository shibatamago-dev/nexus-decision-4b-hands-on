#!/bin/bash
cd "$(dirname "$0")"
exec ./tools/llama-b12441/llama-server \
  -m ./model/nexus-decision-4b.Q4_K_M.gguf \
  --mmproj ./model/nexus-decision-4b.mmproj-Q8_0.gguf \
  --host 127.0.0.1 --port 18080 \
  -c 8192 -t 4
