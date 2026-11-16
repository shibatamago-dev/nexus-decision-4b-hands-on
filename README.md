# nexus-decision-4b ハンズオン

Hugging Face の DecisionPipeline と同じ世代の判断専用モデル **nexus-decision-4b** を、Gemini Decision 1 のハンズオンで使ったのと同じ54問で動かした検証の、再現コードと結果です。

検証記事（下書き）: Zenn に公開予定の比較記事から参照します。
元の54問: [gemini-decision-1-hands-on](https://github.com/shibatamago-dev/gemini-decision-1-hands-on)（54問中53問正解だった Gemini Decision 1 の再現リポジトリ）

## 結果

- **47/54 正解（87.0%）**。Gemini Decision 1 は 53/54 でした。
- カバレッジ（誤差5%以下で自動判断できる割合）は **43/54（79.6%）**。
- 詳しい内訳と実行条件は [RESULTS.md](RESULTS.md) にあります。

## どう動かしたか

公式の経路がそのままでは通らなかったため、著者のプロトコルで動かしています。

- Transformers の DecisionPipeline（main ブランチ）は、モデルが bf16 9.3GB で検証環境（メモリ約6GB）に載らず未実施
- llama.cpp の `/v1/systemone` は HTTP 501（nexus は llama.cpp の対応判断モデルに未登録）
- 採用: llama.cpp（llama-server）の GGUF Q4_K_M＋mmproj で、著者のプロトコル文書どおりのプロンプトを組み、回答位置の文字トークンの logprobs から確率を読む。温度は `nexus_config.json` の fast（0.9752185）。画像は llama.cpp の画像トークン上限256で全問統一

## 使い方

前提: [gemini-decision-1-hands-on](https://github.com/shibatamago-dev/gemini-decision-1-hands-on) を隣のフォルダに置いてください（54問の定義・正解・画像・設計書はそちらから読みます）。

```bash
# 1. llama.cpp のバイナリ (b12441 で検証) と GGUF を model/ に用意
#    - mradermacher/nexus-decision-4b-GGUF の nexus-decision-4b.Q4_K_M.gguf
#    - 同リポジトリの nexus-decision-4b.mmproj-Q8_0.gguf
# 2. サーバ起動
./start_server.sh
# 3. 別ターミナルで実行 (1問ごとに results.json へ保存、途中再開可)
python3 run_nexus.py --smoke   # 疎通確認: テキスト1問 + 画像1問
python3 run_nexus.py           # 全54問
python3 analyze.py             # 正解率・カバレッジ・誤りの内訳を集計
```

## ファイル

| ファイル | 内容 |
| --- | --- |
| `run_nexus.py` | 54問の実行スクリプト（元の `standalone_run.py` を import して質問・正解・判定を共有） |
| `analyze.py` | 正解率・カバレッジ・閾値表・誤りの内訳の集計 |
| `smoke_systemone.py` | llama.cpp `/v1/systemone` の疎通確認（501 が返る記録用） |
| `start_server.sh` | llama-server の起動（GGUF Q4_K_M＋mmproj、画像トークン上限256） |
| `RESULTS.md` | 検証結果ドキュメント |
| `results.json` | 全54問の生の回答と確率 |

## 注意

- GGUF は公式ビルドではなく有志変換（mradermacher）です。著者の公式ビルドは bf16 と MLX 版のみです。
- 54問のうち画像46問は、著者の学習対象（テキストの意図分類など）とは種類が違います。視覚タワーはベースモデル（Qwen3.5-4B）由来のままです。
- 著者の報告値（テスト1,786問でカバレッジ92%など）は著者の計測で、本検証とは前提が違います。
