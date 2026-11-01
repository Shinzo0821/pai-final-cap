# 案A: Colab で Qwen3.5-9B を回す

小さいオープンモデル `Qwen/Qwen3.5-9B`（9.7B、bf16）を Colab の GPU で vLLM の OpenAI 互換サーバーとして立て、
同じランタイムの中で CaP-X を回す。ノートブックは `colab/pai_planA.ipynb`（`colab/build_notebook.py` から生成）。

- タスク: stack・nut・handover（特権情報あり）
- 条件: base／skill（他タスクの成功コードの見本つき、`skill_lib/`）／base_mt（公式の REGENERATE/FINISH の複数ターン）／skill_mt（両方）
- 各10回、合計120試行。結果は `runs/planA/`、集計は `results/planA_*`

## 用意するもの

1. **Colab Pro** と GPU のランタイム（**A100** をすすめる。実際に回したのは A100。下の「GPU の選び方」）。
   「ランタイム」→「ランタイムのタイプを変更」で選ぶ。手元の Colab CLI で回すときは下の「Colab CLI で回すとき」。
2. リポジトリの取り方（非公開なので、どちらか）
   - **シークレット（おすすめ）**: Colab の左の鍵マークに次を登録し、「ノートブックからのアクセス」をオンにする。
     - `GITHUB_TOKEN`: GitHub の Fine-grained トークン。対象はこのリポジトリだけ、権限は Contents: Read-only。
     - `GITHUB_REPO`: `<アカウント名>/pai-final-cap`
     - （任意）`HF_TOKEN`: Hugging Face のトークン。無くてよい（Qwen3.5-9B は公開モデル）。あるとダウンロードの制限が緩む。
   - **zip**: GitHub の「Code → Download ZIP」（ブランチ `main`）で落とし、セル2でアップロードする。
   トークンは表示も保存もしない（clone のときだけ環境変数で渡し、URL や `.git/config` に残さない）。
3. ノートブックを Colab で開く: GitHub から開くか、`colab/pai_planA.ipynb` をアップロードする。

## 押す順番

上から1つずつ実行する（「すべてのセルを実行」でもよいが、2 と 7 は入力や許可を求める）。

| セル | すること | 時間（A100 で実測） |
|---|---|---|
| 0 | 設定とヘルパー。ふつうは変えない | すぐ |
| 1 | GPU の種類・メモリ・ドライバー、CPU コア数を表示。並列数（`WORKERS`）を決める | すぐ |
| 2 | リポジトリの取得（シークレット → 無ければ zip のアップロード） | 1分 |
| 3 | CaP-X の導入（`colab/setup_capx.sh`。apt の描画ライブラリ、CaP-X の固定の commit、パッチ、Python 3.12 の venv） | 3〜4分 |
| 4 | 描画の方式を決める（EGL を試し、だめなら OSMesa）。使った方式と `GL_RENDERER` を環境メモに残す | 1分 |
| 5 | vLLM を別の venv に入れる | 1〜3分 |
| 6 | vLLM で Qwen3.5-9B を立て、記録用の中継（ポート 8120）をつなぐ | 6.5分（ダウンロード約18GB と初回の JIT を含む） |
| 6b | 1回試す（短い返事と、stack のプロンプト）。`<think>` が出ないこと、出力の速さを確かめる | 1〜2分 |
| 7 | Google Drive をマウントし、途中経過の復元と5分ごとのコピーを始める | 1分 |
| 8 | oracle（正解コード）を3タスク×3回。3つとも 3/3 になること | 3分 |
| 9 | Qwen で1試行だけ（skill_mt・stack） | 1分 |
| 10 | 本番を裏で開始（4条件×3タスク×10回）。止まった試行の見張り（`colab/watchdog.py`）も起動 | すぐ終わる（本番は 1 時間 25 分） |
| 11 | 進み具合を1分ごとに表示（止めても本番は続く） | 本番が終わるまで |
| 12 | 集計（`results/planA_*`）、見本が入っていたか、10 試行に足りないセルと断られた呼び出しの確認 | すぐ |
| 13 | 環境メモ（`runs/planA/ENV_planA.md`） | すぐ |
| 14 | 結果を zip にして Drive に置き、ダウンロード | 1分 |

## 途中で止まったとき（再開）

- 本番（`scripts/run_grid.py`）は `DONE` のあるセルを飛ばす。**同じセル 10 をもう一度実行すれば続きから回る**。
  途中だったセルは最初からやり直す。
- ランタイムが切れたら、新しいランタイムで**上から順に**実行する。セル7が Drive（`マイドライブ/pai_planA/`）から
  `runs/`・`logs/`・`results/` を戻すので、セル10で続きから回る。5分ごとのコピーなので、最後の数分ぶんはやり直しになる。
- 本番の開始時刻は `logs/planA_start.txt` に残り、集計はそれより前の呼び出し（試しの分）を数えない。

## GPU の選び方

- **A100（40GB）をすすめる**。案A の本番はこれで回した（重み 16.8GiB、KV キャッシュ 15GiB ≒ 44 万トークン分、出力 約 72 トークン/秒）。
- 決め手は**文脈の長さ**。CaP-X は毎回 `max_tokens` 20480 を送る（CaP-X の既定。`run_grid.py` は変えない）。vLLM は
  「プロンプト＋20480」が `--max-model-len` を超える呼び出しを 400 で断り、CaP-X はその試行を記録から落とす。
  複数ターンではプロンプトが伸び、本番の最大は 23,029 トークンだった。なので `--max-model-len` は 65536（既定）にする。
  32768 では、プロンプトが 12,288 トークンを超えた呼び出しが断られる（実際に 1 回目の実行で、複数ターンの 3 セルから 7 試行が落ちた）。
- **L4（24GB）**は重みを載せると KV キャッシュが数 GB しか残らず、65536 で立ち上がるかは確かめていない。
  セル6は 65536 → eager → 32768 の順に試し、32768 で立ち上がったら警告を出す。20480 より小さい上限では全部の呼び出しが断られる。
- G4（RTX PRO 6000、96GB、48 コア）は余裕があるが、このアカウントでの vLLM の動作は確かめていない。並列数（最大 5）を上げないと
  コア数は活きない。**T4（16GB）は使えない**（重みが載らない）。H100 はこのアカウントでは選べない。
- 描画は A100 でも NVIDIA の EGL で動く（OSMesa の約 16 倍）。handover の oracle 3 試行が 88〜106 秒。

## 所要時間とコンピューティングユニット（A100 で実測）

- 準備（セル1〜9）: 約 25 分。本番（120 試行、並列 5）: 1 時間 25 分。集計と zip: 数分。合計 2 時間ほど。
  - 長いのは handover の複数ターン（skill_mt で 2,068 秒）。stack・nut は 1 セル数分。
- ユニット: A100 は 1 時間あたり約 5.4（他の人が測った値。Colab の「リソースを表示」で確かめる）。合計 2 時間なら 11 前後。
- 終わったらすぐ「ランタイムを接続解除して削除」（CLI なら `colab stop`）する。つないでいる間はユニットが減る。

## Colab CLI で回すとき（手元の `colab` コマンド）

Web UI ではなく、手元の Colab CLI で回すこともできる（案A の本番はこれで回した）。セルの中身を順に `colab exec` で実行する。

- **手元の Mac を眠らせない**。CLI の接続が切れると、Colab は VM を回収することがある（実際に 2 回、VM ごと結果が消えた）。
  `caffeinate -i -t <秒>` を本番の長さだけ動かし、蓋を閉じない。
- **途中経過はこまめに手元に回収する**。セル7（Drive）は対話が要るので CLI では使えない。代わりに `runs/`・`logs/`・`results/` を
  zip にして `colab download` で取ってくる（1 セル終わるごと、または 20 分ごと）。終わったら、返事を待つ前に集計と回収まで済ませる。
- セル2の clone の代わりに、`git archive` の zip を `colab upload` して `/content` に展開する（セル2は「取得済み」になる。
  commit は記録されないので、環境メモの `repo` を手で直す）。
- `colab exec` は既定で 30 秒で手元が打ち切る（VM 側は続く）。長いセルは `--timeout` を長く付ける。また、ときどき接続が切れて
  手元のコマンドが固まるので、手元の側にも時間の上限を付ける（macOS なら `perl -e 'alarm shift; exec @ARGV' <秒> colab ...`）。
- `colab exec` は実行のたびに作業ディレクトリを `/content` に戻す。セル3以降は先頭で `os.chdir(REPO_DIR)` するようにしてある。
- セル14の `files.download` は CLI では効かない。zip は `colab download` で取ってくる。

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
   │  POST model・messages・temperature 1.0・max_tokens 20480（CaP-X の既定）
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
- **サンプリング**: 温度は CaP-X が送る 1.0（CaP-X の既定。以前ここに 0.2 と書いていたのは誤り）。そのほか（top_p など）はモデルの `generation_config.json` の既定（vLLM の既定の動き）。
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
| セル6で立ち上がらない（メモリ不足） | 自動で eager・32768 まで試す。だめなら A100 か G4 に替える（上の「GPU の選び方」） |
| セル6で `FileNotFoundError: ... 'ninja'`（CUDA グラフのウォームアップで落ちる） | vLLM の venv の `bin` が PATH に無い。セル6は足して起動するようにしてある。手で起動するときも `PATH=/content/vllm-venv/bin:$PATH` にする |
| 試行の数が 10 に足りないセルがある（`launch.log` に `400 Client Error`） | 文脈の長さの不足（上の「GPU の選び方」）。`--max-model-len` を上げて vLLM を立て直し、そのセルの `DONE` を消してセル10をもう一度実行 |
| セル6b で `<think>` が出る | 自動で中継の `--force-no-think` に切り替わる。環境メモの `force_no_think` を見る |
| セル4で `GL_RENDERER` が llvmpipe | EGL がソフトウェア描画になっている。動くが速くはならない。そのまま進めてよい |
| oracle が 3/3 にならない | 描画か環境の問題。`GL_BACKEND = "osmesa"` にしてセル4からやり直す |
| handover の試行が 1000 秒で打ち切られる | CaP-X の試行時間の上限（`TRIAL_TIMEOUT_SECONDS`）。CaP-X が自動でやり直す。数が多ければ `VIDEO_TRIALS = 0` にする |
| 1 つの試行が 1000 秒を過ぎても終わらない（作業プロセスが CPU を使い切ったまま） | CaP-X の時間切れが生成コードの `except` に捕まって効いていない。見張り（`colab/watchdog.py`）が 20 分で合図を送り直す。手でなら `kill -ALRM <pid>` |
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

## Colab の A100 で回して確かめたこと（2026-11-01、Colab CLI で）

- vLLM 0.31.0（torch 2.13 / CUDA 13.0）が A100 で立ち上がる（65536、CUDA グラフあり、PATH の修正込み）。thinking は切れる
  （289 回中 `<think>` で始まる返事は 0。返事の途中に `</think>` が紛れたのが 2 回）。
- NVIDIA の EGL で描画できる。oracle は stack・nut 3/3、handover は 2/3 と 3/3（`runs/planA/ENV_planA.md`）。
- 本番 120 試行が抜けなく終わり、見張りの合図は 0 回、vLLM のエラーは 0 回。結果は `results/planA_*`。

確かめていないこと: Web UI から押した場合（シークレットでの clone、zip のアップロード、Drive のマウントと定期コピー）、
L4・G4 での vLLM の起動、この版のノートブック（直したあと）を上から通すこと。直したところ（セル6の PATH と上限、セル6b の温度、
セル10の見張り、セル12・13）は、A100 での実行で手で入れて動いたものを、ノートブックに書き戻した。
