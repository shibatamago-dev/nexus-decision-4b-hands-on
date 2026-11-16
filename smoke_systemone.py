"""llama.cpp の /v1/systemone が nexus-decision-4b (GGUF) で使えるかの疎通確認。

llama.cpp の systemone は対応が登録された判断モデル専用で、対象外モデルには
501 を返す仕様 (tools/server/README.md)。結果をそのまま記録するためのスクリプト。
使い方: llama-server 起動後に python3 smoke_systemone.py
"""
import json
import urllib.error
import urllib.request

SERVER = "http://127.0.0.1:18080"
payload = {
    "state": "Customer message: I was charged twice for order #4471, please fix it today.",
    "questions": {
        "route": {"type": "choice", "instructions": "Which queue should handle this?",
                  "criteria": {"billing": "Payments, refunds, double charges",
                               "shipping": "Delivery problems",
                               "needs_review": "Anything else or unclear"}},
        "urgent": {"type": "noul", "instructions": "The customer needs a same-day response."},
    },
}
req = urllib.request.Request(SERVER + "/v1/systemone",
                             data=json.dumps(payload).encode(),
                             headers={"Content-Type": "application/json"}, method="POST")
try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        print("HTTP", resp.status)
        print(json.dumps(json.loads(resp.read()), ensure_ascii=False, indent=2))
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode("utf-8", "replace")[:1000])
