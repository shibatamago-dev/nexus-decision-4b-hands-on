# 検証結果: nexus-decision-4b を Gemini Decision 1 と同じ54問で試した

実行日: 2026-11-17（JST）。検証の設計とコードはこのリポジトリの README と各スクリプトを参照。

## まとめ

| 指標 | nexus-decision-4b（今回） | Gemini Decision 1（前回） |
| --- | --- | --- |
| 正解率 | **47/54（87.0%）** | 53/54（98.1%） |
| カバレッジ（誤差5%以下で自動判断できる割合） | **43/54（79.6%）** | （前回は未計測） |
| テキストのみ（設計書8問） | 7/8 | 8/8 |
| 画像46問 | 40/46 | 45/46 |

カバレッジの定義は nexus-decision-4b の著者の報告と同じ（全回答を確信度の高い順に並べ、誤差率が5%以下に収まる最大の prefix の割合）。

確信度の閾値ごとの内訳（今回）:

| 閾値 | 自動判断できる割合 | その誤差率 |
| --- | --- | --- |
| ≥0.90 | 40/54（74.1%） | 5.0% |
| ≥0.95 | 36/54（66.7%） | 2.8% |
| ≥0.99 | 27/54（50.0%） | 0.0% |

## 実行条件

| 項目 | 内容 |
| --- | --- |
| モデル | zackyalgiffari/nexus-decision-4b（HF revision `a82d53bb716548736ae13b0bbdce0ec168299e83`、Apache-2.0） |
| 量子化 | GGUF Q4_K_M + mmproj Q8_0（`mradermacher/nexus-decision-4b-GGUF`。公式ビルドではなく有志変換） |
| 実行基盤 | llama.cpp b12441（llama-server、CPU推論） |
| 読み方 | 著者のプロトコル文書どおりのプロンプト＋回答位置の文字トークン（A, B, C, …）の logits。温度は `nexus_config.json` の fast = 0.9752185 |
| 画像の扱い | llama.cpp の画像トークン上限 256（`--image-max-tokens 256`）。全問で条件を統一 |
| 質問と正解 | Gemini Decision 1 ハンズオンの `standalone_run.py` をそのまま import（11ケース・54問、判定ロジックも同一） |
| 環境 | Muse の VM（共有CPU 1.5コア／メモリ約6GB）。1問あたり約70秒かかったが、これはこの環境の数字でモデルの速度ではない |

## 経路の疎通結果（DecisionPipeline まわり）

「HF の DecisionPipeline で nexus をそのまま動かす」は、今回の環境では3経路とも素直には通らなかった。

1. **Transformers の DecisionPipeline（main ブランチ）**: モデル本体が bf16 で 9.3GB あり、メモリ約6GBのこの VM には載らないため未実施。DecisionPipeline 自体は任意のチャットモデルを文字 logits で読む設計で、nexus 専用の `decision.json` はリポジトリに同梱されていない。
2. **llama.cpp の `/v1/systemone`**: 疎通確認の結果、HTTP 501 `{"message":"This model is not a decision model"}`。llama.cpp の systemone は対応が登録された判断モデル専用で、nexus-decision-4b（通常の Qwen3.5 GGUF 変換）は対象外だった。
3. **著者プロトコル＋logprobs（採用）**: 著者の GitHub リポジトリのプロトコル文書どおりにプロンプトを組み、llama-server のチャット API の logprobs から文字トークンの確率を読んだ。著者の公式実装（`nexus_decision` パッケージの HF バックエンド）と同じ読み方。

## 誤りの内訳（7問）

| ケース | 質問 | 正解 | モデルの答え | 確信度 |
| --- | --- | --- | --- | --- |
| realistic/bear-distant.jpg | has_bear（クマはいるか） | True | False | 0.941 |
| realistic/bear-distant.jpg | has_large_animal | True | False | 0.596 |
| realistic/bear-distant.jpg | what_animal | bear | deer | 0.438 |
| bear/forest-dog.png | has_large_animal | True | False | 0.689 |
| bear/forest-dog.png | proximity（近さ 0〜2） | 1.0 | 1.81 | 0.810 |
| design_doc | has_nonfunctional（非機能要件はあるか） | False | True | **0.987** |
| waldo | is_in_middle-center | False | True | 0.544 |

読み取れること:

- **遠くのクマ（bear-distant.jpg）に集中**（3問）。小さい被写体は画像トークン上限256の圧縮で不利になった可能性があるため、参考計測として上限なしでこの4問だけ再実行した結果を末尾に置く。
- **イヌを「大きな動物」としない**のは Gemini Decision 1 の唯一の誤りと同じ傾向（forest-dog の has_large_animal）。「大きな動物」の解釈が両モデルともイヌで割れている。
- **設計書の has_nonfunctional は確信度 0.987 の誤り**。テキストは著者の主戦場のはずで、ここでの高確信度の外しは校正の限界として目立つ。設計書には非機能要件の章がない（性能・セキュリティ等への言及なし）が、モデルは「ある」と答えた。
- ウォーリーの隣マス誤認（is_in_middle-center）は確信度 0.544 と低く、閾値で人間に回す運用なら防げるタイプ。

## ケース別

| ケース | 結果 |
| --- | --- |
| waldo（群衆から探す、10問） | 9/10 |
| design_doc（設計書、8問） | 7/8 |
| road/road-clean.png | 4/4 |
| road/road-luggage.png | 4/4 |
| bear/forest-none.png | 4/4 |
| bear/forest-bear.png | 4/4 |
| bear/forest-dog.png | 2/4 |
| realistic/bear-close.jpg | 4/4 |
| realistic/bear-distant.jpg | 1/4 |
| realistic/dog.jpg | 4/4 |
| realistic/empty.jpg | 4/4 |

種類別: choice 9/10、noul 29/34、score 9/10。

## 著者報告値との違い

著者（Zacky Al Giffari）の報告は**未検証の報告**として扱う。前提が大きく違うため、数字を直接比べることはできない。

| | 著者報告 | 今回 |
| --- | --- | --- |
| テスト | 1,786問（BANKING77 / CLINC150 の意図分類＋合成シナリオ、テキストのみ） | 54問（画像46＋テキスト8） |
| 正解率 | 0.915（人間ラベル1,200問） | 0.870（54問） |
| カバレッジ@誤差5% | 92% | 79.6% |
| 実行形態 | bf16 本家ビルド（L4 GPU 等） | GGUF Q4_K_M 量子化（CPU） |

違いの主な要因として考えられるもの: (1) 画像46問は著者の学習対象外（視覚タワーはベースの Qwen3.5-4B 由来のままで、判断用に学習されていない）、(2) 量子化（著者は MLX 4bit/8bit で bf16 と 50/50 一致と報告しているが、GGUF Q4_K_M での一致は未検証）、(3) 画像トークン上限256の圧縮、(4) そもそも54問では1問の重みが約1.9ポイントあり統計的に粗い。

## 参考計測: 遠くのクマを画像トークン上限なしで再実行

bear-distant.jpg の4問だけ、画像トークン上限なし（プロンプト約1,230トークン）で再実行した。

| 質問 | 上限256（本計測） | 上限なし（参考） |
| --- | --- | --- |
| has_bear | False・確信度0.941（誤り） | False・確信度0.615（誤り） |
| has_large_animal | False（誤り） | True（正解） |
| what_animal | deer（誤り） | other_animal（誤り） |
| proximity | 正解 | 正解 |

上限なしでは 2/4（上限256では 1/4）。圧縮の影響は最大で1問分で、has_bear は上限なしでも外した（ただし確信度は 0.941 → 0.615 に下がり、閾値運用では人間に回しやすくなる）。「遠くの小さいクマが苦手」という結論は上限なしでも変わらなかった。

## 再現方法

```bash
# llama.cpp b12441 のバイナリと GGUF を用意し、サーバを起動
./start_server.sh
# 別ターミナルで（54問の定義は gemini-decision-1-hands-on を隣に置く）
python3 run_nexus.py
python3 analyze.py
```
