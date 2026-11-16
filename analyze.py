"""results.json から、正解率・カバレッジ (誤差5%以下で自動判断できる割合)・
閾値表・誤りの内訳を集計して analysis.json と Markdown 表を出す。

カバレッジの定義は nexus-decision-4b 著者の報告と同じ:
  全回答を確信度の高い順に並べ、誤差率が5%以下に収まる最大の prefix の割合。
score 問題の確信度は分布の最大確率、正誤は元の検証と同じ |got-expected|<=0.6。
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
data = json.loads((BASE / "results.json").read_text(encoding="utf-8"))

rows = []
for r in data["results"]:
    for qid, v in r["verdicts"].items():
        ans = r["answers"][qid]
        rows.append({"case": r["case"], "qid": qid, "type": ans["type"],
                     "pass": v["pass"], "confidence": ans.get("confidence"),
                     "expected": v["expected"], "got": v.get("got")})

total = len(rows)
passed = sum(1 for x in rows if x["pass"])
print(f"accuracy: {passed}/{total} = {passed/total:.3f}")

# カバレッジ (誤差5%以下)
srt = sorted(rows, key=lambda x: -x["confidence"])
best = 0
errs = 0
for i, x in enumerate(srt, 1):
    errs += 0 if x["pass"] else 1
    if errs / i <= 0.05:
        best = i
print(f"coverage@5%error: {best}/{total} = {best/total:.3f}")

# 閾値表
for th in (0.5, 0.8, 0.9, 0.95, 0.99):
    sel = [x for x in rows if x["confidence"] >= th]
    if sel:
        e = sum(1 for x in sel if not x["pass"]) / len(sel)
        print(f"conf>={th}: n={len(sel)} ({len(sel)/total:.1%}) error={e:.1%}")

# ケース別
from collections import defaultdict
by = defaultdict(lambda: [0, 0])
for x in rows:
    by[x["case"]][1] += 1
    by[x["case"]][0] += 1 if x["pass"] else 0
for k, (p, t) in by.items():
    print(f"{k}: {p}/{t}")

# 種類別
by = defaultdict(lambda: [0, 0])
for x in rows:
    by[x["type"]][1] += 1
    by[x["type"]][0] += 1 if x["pass"] else 0
for k, (p, t) in by.items():
    print(f"type {k}: {p}/{t}")

print("\nmisses:")
for x in rows:
    if not x["pass"]:
        print(f"  {x['case']} :: {x['qid']} expected={x['expected']!r} got={x['got']!r} conf={x['confidence']:.3f}")

# テキストのみ (design_doc) の部分集計
txt = [x for x in rows if x["case"] == "design_doc"]
tp = sum(1 for x in txt if x["pass"])
print(f"\ntext-only (design_doc): {tp}/{len(txt)}")
img = [x for x in rows if x["case"] != "design_doc"]
ip = sum(1 for x in img if x["pass"])
print(f"image questions: {ip}/{len(img)}")

(BASE / "analysis.json").write_text(json.dumps(
    {"total": total, "passed": passed, "coverage_at_5pct": best,
     "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
