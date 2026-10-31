# 案A: Colab で Qwen3.5-9B を回す

小さいオープンモデル `Qwen/Qwen3.5-9B`（9.7B、bf16）を Colab の GPU で vLLM の OpenAI 互換サーバーとして立て、
同じランタイムの中で CaP-X を回す。ノートブックは `colab/pai_planA.ipynb`（`colab/build_notebook.py` から生成）。

- タスク: stack・nut・handover（特権情報あり）
- 条件: base／skill（他タスクの成功コードの見本つき、`skill_lib/`）／base_mt（公式の REGENERATE/FINISH の複数ターン）／skill_mt（両方）
- 各10回、合計120試行。結果は `runs/planA/`、集計は `results/planA_*`

## 用意するもの

1. **Colab Pro** と GPU のランタイム（既定は **L4**）。「ランタイム」→「ランタイムのタイプを変更」で選ぶ。
2. リポジトリの取り方（非公開なので、どちらか）
   - **シークレット（おすすめ）**: Colab の左の鍵マークに次を登録し、「ノートブックからのアクセス」をオンにする。
     - `GITHUB_TOKEN`: GitHub の Fine-grained トークン。対象はこのリポジトリだけ、権限は Contents: Read-only。
     - `GITHUB_REPO`: `<アカウント名>/pai-final-cap`
     - （任意）`HF_TOKEN`: Hugging Face のトークン。無くてよい（Qwen3.5-9B は公開モデル）。あるとダウンロードの制限が緩む。
   - **zip**: GitHub の「Code → Download ZIP」（ブランチ `plana-colab`）で落とし、セル2でアップロードする。
   トークンは表示も保存もしない（clone のときだけ環境変数で渡し、URL や `.git/config` に残さない）。
3. ノートブックを Colab で開く: GitHub から開くか、`colab/pai_planA.ipynb` をアップロードする。

## 押す順番

上から1つずつ実行する（「すべてのセルを実行」でもよいが、2 と 7 は入力や許可を求める）。

| セル | すること | 時間の目安（L4） |
|---|---|---|
| 0 | 設定とヘルパー。ふつうは変えない | すぐ |
| 1 | GPU の種類・メモリ・ドライバー、CPU コア数を表示。並列数（`WORKERS`）を決める | すぐ |
| 2 | リポジトリの取得（シークレット → 無ければ zip のアップロード） | 1分 |
| 3 | CaP-X の導入（`colab/setup_capx.sh`。apt の描画ライブラリ、CaP-X の固定の commit、パッチ、Python 3.12 の venv） | 5〜10分 |
| 4 | 描画の方式を決める（EGL を試し、だめなら OSMesa）。使った方式と `GL_RENDERER` を環境メモに残す | 1分 |
| 5 | vLLM を別の venv に入れる | 5〜10分 |
| 6 | vLLM で Qwen3.5-9B を立て、記録用の中継（ポート 8120）をつなぐ | 5〜15分（初回はダウンロード約19GB） |
| 6b | 1回試す（短い返事と、stack のプロンプト）。`<think>` が出ないこと、出力の速さを確かめる | 1〜2分 |
| 7 | Google Drive をマウントし、途中経過の復元と5分ごとのコピーを始める | 1分 |
| 8 | oracle（正解コード）を3タスク×3回。3つとも 3/3 になること | 5〜10分 |
| 9 | Qwen で1試行だけ（skill_mt・stack） | 2〜5分 |
| 10 | 本番を裏で開始（4条件×3タスク×10回） | すぐ終わる |
| 11 | 進み具合を1分ごとに表示（止めても本番は続く） | 本番が終わるまで |
| 12 | 集計（`results/planA_*`）と、見本が入っていたかの確認 | すぐ |
| 13 | 環境メモ（`runs/planA/ENV_planA.md`） | すぐ |
| 14 | 結果を zip にして Drive に置き、ダウンロード | 1分 |

## 途中で止まったとき（再開）

- 本番（`scripts/run_grid.py`）は `DONE` のあるセルを飛ばす。**同じセル 10 をもう一度実行すれば続きから回る**。
  途中だったセルは最初からやり直す。
- ランタイムが切れたら、新しいランタイムで**上から順に**実行する。セル7が Drive（`マイドライブ/pai_planA/`）から
  `runs/`・`logs/`・`results/` を戻すので、セル10で続きから回る。5分ごとのコピーなので、最後の数分ぶんはやり直しになる。
- 本番の開始時刻は `logs/planA_start.txt` に残り、集計はそれより前の呼び出し（試しの分）を数えない。

## GPU の選び方

- Qwen3.5-9B の重みは bf16 で約 19GB（9.7B × 2 バイト）。**L4（24GB）**では残りが数 GB しかないので、
  セル6は `--max-model-len 32768` で試し、立ち上がらなければ 16384、さらに `--enforce-eager` を自動で試す。
  プロンプトは最大でも数千トークン（見本つきで約3,500）＋出力 4,096 なので、16384 でも足りる見込み。
- それでも立ち上がらないとき（ログに `CUDA out of memory` や「KV cache が足りない」）は **G4 か A100** に替える:
  1. セル14までの結果が要るなら、先に Drive に写っていることを確かめる（セル7を実行していれば5分ごとに写る）。
  2. 「ランタイム」→「ランタイムのタイプを変更」→ G4 か A100 → 保存（ランタイムは作り直される）。
  3. 上から順に実行し直す。セル1で GPU を確かめる。vLLM の版はドライバーに合わせて自動で選ぶ。
- **T4（16GB）は使えない**（重みが載らない。bf16 にも対応していない）。H100 はこのアカウントでは選べない。
- 出力の速さは GPU のメモリ帯域で決まる。L4（約 300GB/s）では1本あたり十数トークン/秒の見込みで、
  1回の回答（数百〜千数百トークン）に 1 分前後かかる。A100・G4（約 1.5〜2TB/s）は数倍速い。
  セル6b が実際の速さ（`tokens_per_s`）を環境メモに残す。

## 所要時間とコンピューティングユニットの目安

あくまで見積もり（Qwen の実機ではまだ測っていない）。

- 準備（セル1〜9）: 30〜50分。
- 本番（120試行）: L4 で 1.5〜3 時間の見込み。
  - LLM の呼び出しは、1回で答える条件が 60 回、複数ターンの条件が 60 試行 × 2〜4 回。並列 5 本なら、L4 で合計 30〜60 分ほど。
  - シミュレーションは handover が重い（クラウドの CPU 描画で 10 試行 3,305 秒）。動画は各セルの最初の 2 試行だけにした
    （`VIDEO_TRIALS`）。EGL が GPU で動けば描画はさらに速くなる。
  - A100・G4 は LLM の部分が数倍速いので、本番は 1〜2 時間の見込み。
- ユニット: 消費の速さは Colab の「リソースを表示」に「1 時間あたり ◯ ユニット」と出るので、それで掛け算する。
  これまでの公表値の目安は L4 が 1 時間あたり 5 前後、A100 が 12〜15 前後（G4 は確かめていない）。
  L4 で合計 3〜4 時間なら 15〜20 ユニット、A100 で 2〜3 時間なら 25〜45 ユニットほどで、残り約 145 ユニットに収まる。
- 終わったらすぐ「ランタイムを接続解除して削除」する（つないでいる間はユニットが減る）。

## 何が残るか（セル14の zip）

- 各セル: `launch.log`・`DONE`・`summary.csv`・CaP-X のセル単位のファイル（`initial_prompt.txt`・`all_responses.json`・`summaries.txt`）
- 各試行: `summary.txt`・`code.py`・`all_responses.json`、動画 `video_combined.mp4`（各セルの最初の2試行だけ）
- `logs/llm_calls.jsonl`: vLLM への全呼び出し（送った messages、返事、トークン数、所要時間、`<think>` の有無）
- `logs/vllm_tail.log`（vLLM のログの最後）、`logs/run_planA.log`、`logs/gl_check.json`（描画の確認）
- `runs/planA/ENV_planA.md`（環境メモ）と `planA_env.json`（その材料）、`results/planA_*`（集計）
- oracle（`runs/planA_oracle`）と1試行（`runs/planA_try`）の結果

## しくみ

```
CaP-X (scripts/run_grid.py, --workers N)
   │  POST model・messages・temperature 0.2・max_tokens 4096
   ▼
proxy/log_proxy.py :8120  ── 全呼び出しを logs/llm_calls.jsonl に記録（中身は変えない）
   ▼
vLLM :8000  Qwen/Qwen3.5-9B（served-model-name qwen3.5-9b）
   --language-model-only --default-chat-template-kwargs '{"enable_thinking": false}'
```

- **thinking を切る**: CaP-X は `chat_template_kwargs` を送らないので、vLLM の既定を
  `--default-chat-template-kwargs '{"enable_thinking": false}'` にする（要求の値があればそちらが優先され、無ければ既定が使われる）。
  セル6b で `<think>` が出たら、中継が `chat_template_kwargs.enable_thinking=false` を足す設定（`--force-no-think`）に自動で切り替え、
  環境メモに残す。
- **文字だけで使う**: Qwen3.5 は画像も読めるモデル。`--language-model-only` で画像の部分を読み込まない。
- **サンプリング**: 温度は CaP-X が送る 0.2。そのほか（top_p など）はモデルの `generation_config.json` の既定（vLLM の既定の動き）。
- **描画**: `MUJOCO_GL=egl`（`PYOPENGL_PLATFORM=egl`）を試し、動かなければ `osmesa`。Colab では NVIDIA の EGL が
  登録されていないことがあるので、セル4が `/usr/share/glvnd/egl_vendor.d/10_nvidia.json` を作る（MuJoCo の公式 Colab と同じ）。
- **動画は最初の N 試行だけ**: `run_grid.py --video-trials N`。CaP-X 側は環境変数 `CAPX_VIDEO_TRIALS` を見て、
  N より後の試行では動画を記録しない（`patches/capx.patch` の `capx/envs/trial.py`）。
- **並列数**: `WORKERS = min(5, CPU コア数 − 2)`（IK サーバー・vLLM・描画に CPU を残す。10試行を2巡）。

## vLLM の版の確かめ方（この準備でやったこと）

- `vllm==0.31.0`（2026-10-05、PyPI）と `vllm==0.19.1`（2026-04、PyPI）のソースで、
  `Qwen3_5ForConditionalGeneration` の登録、`--language-model-only`（画像の部分を読み込まない処理につながっている）、
  `--default-chat-template-kwargs`（チャットテンプレートに既定値として渡される）があることを確かめた。
- 両方を実際に pip で入れ、vLLM 自身の引数パーサーでセル6の引数を解釈させ、
  `default_chat_template_kwargs={'enable_thinking': False}`・`language_model_only=True` になることを確かめた
  （GPU が無いので、機種の判定だけ飛ばした）。
- PyPI の 0.31.0 は torch 2.13（CUDA 13.0）、0.19.1 は torch 2.10（CUDA 12.8）。CUDA 13 には新しいドライバーが要るので、
  セル5はドライバーの CUDA の版を見て選び、0.31.0 で GPU が使えなければ 0.19.1 に替える。

## 困ったとき

| 症状 | 対処 |
|---|---|
| セル6で立ち上がらない（メモリ不足） | 自動で 16384・eager まで試す。だめなら G4 か A100 に替える（上の「GPU の選び方」） |
| セル6b で `<think>` が出る | 自動で中継の `--force-no-think` に切り替わる。環境メモの `force_no_think` を見る |
| セル4で `GL_RENDERER` が llvmpipe | EGL がソフトウェア描画になっている。動くが速くはならない。そのまま進めてよい |
| oracle が 3/3 にならない | 描画か環境の問題。`GL_BACKEND = "osmesa"` にしてセル4からやり直す |
| handover の試行が 1000 秒で打ち切られる | CaP-X の試行時間の上限（`TRIAL_TIMEOUT_SECONDS`）。CaP-X が自動でやり直す。数が多ければ `VIDEO_TRIALS = 0` にする |
| 本番が止まった | セル11で最後のログを見て、セル10をもう一度実行（続きから） |

## この環境（GPU なし）での試運転で確かめたこと

- `colab/setup_capx.sh` で CaP-X を一から入れ、oracle を 3タスク×3回 → 3つとも 3/3（OSMesa）。
  ただし、別の重い処理（CaP-X の導入）と同時に回したときに一度だけ nut が 2/3 になった（同じ試行番号でも結果が変わった。
  コードは最後まで動き、ナットが入らなかった）。何もしていないときに回し直すと 3/3。CPU の負荷で動きがずれるらしいので、
  Colab で nut が1回落ちる程度なら環境の故障とは限らない。
- ダミーのモデル（`proxy/dummy_llm.py`、決まった回答を返す）で 4条件×3タスク×各1試行を最後まで通した。
  複数ターンでは REGENERATE → 実行 → FINISH の2ブロックになり、`scripts/check_skill_prompts.py` で
  「送ったプロンプトに見本が入り、見本を除くと base と完全に一致」を確認、`scripts/analyze.py --tag planA` の集計も出た。
- ノートブックを Jupyter のカーネルで上から最後まで実行（`PLANA_DRY_RUN=1`。vLLM の代わりにダミー、Drive の代わりにローカルのフォルダ）。
- 描画の切り替え: この環境では EGL も（ソフトウェアで）動き、EGL を壊すと OSMesa に切り替わることを確認。CaP-X も EGL で1試行通った。

確かめていないこと: Colab の GPU での vLLM の起動とメモリ、Qwen3.5-9B の実際の回答と速さ、NVIDIA の EGL、Drive のマウント、
シークレットでの clone と zip のアップロード（Colab 固有の部分）。
