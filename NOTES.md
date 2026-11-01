# 作業メモ（PAI 応用編1 最終課題）

締切: 2026-11-02(月) 10:00。提出物は YouTube 動画（1〜3分）、PDF レポート、公開 GitHub。

## テーマ
CaP-X（Code-as-Policy のベンチマーク）で、LLM ごとにロボット制御コードの書きやすさを比べる。GENIAC-PRIZE 本コンテスト（Code-as-Policy）の下準備も兼ねる。

## ここまで（2026-10-30）
- CaP-X を `../third_party/cap-x` に置き、Mac 用の仮想環境 `.venv-mac` を作った（Python 3.12、mujoco==3.5.0、scipy<1.15、numpy==1.26.4 に固定）。
- CaP-X の変更点: `capx/llm/client.py` の LLM 待ち時間を環境変数 `CAPX_LLM_TIMEOUT` で変えられるようにした（既定 200 秒）。
- `proxy/cli_proxy.py`: Claude Code / Codex CLI を OpenAI 互換の API として見せる中継サーバー。モデル名は `claude-cli/<model>`、`codex-cli/<model>@<effort>`。
- 動作確認: Sonnet 5.5 でキューブ持ち上げ成功、gpt-6-sol でキューブ積み成功（各1回）。
- 正解コード（特権情報あり）を各3回: cube_stack・cube_restack・spill_wipe・nut_assembly・handover は 3/3、two_arm_lift は 1/3。
- 使えるモデル: Claude Sonnet 5.5・Haiku 5.5、Codex gpt-6-sol・gpt-6-astra・gpt-5.6-sol。Opus 5.5 は Claude CLI を 2.1.280 以上に上げる必要がある。

## 2026-10-31 の進み具合
- Claude CLI を 2.1.314 に更新（Opus 5.5 が使える）。agy（Antigravity CLI）も中継サーバーにつないだ。
- 拡張 `pai_ext/`: 位置に誤差を足す（*_Noisy）・掴み方の補助を外す（*_NoGrasp）API。CaP-X への変更は `patches/capx.patch`。
- 条件の設定は `scripts/make_configs.py` で `configs/` に生成（base_mt / noisy / noisy_mt / nograsp）。
- IK サーバー（PyRoKi）は macOS で並行処理すると固まることがある。`run_grid.py` が応答を確かめ、失敗した組み合わせは立て直してやり直す。
- 予備実験（runs/pilot）: 積む・ナット・拭くは軽いモデルでも満点。積み替えは全モデル 0/3（初期状態で緑が赤の上にある）。受け渡しは上位がやや強い。
- 正解コード（runs/oracle）: 誤差 1cm で積む・積み替え・ナットが 0/5、平均化すれば 4/5・5/5・3/5。
- 本番モデル（ユーザーと決定）: Haiku 5.5 / Opus 5.5、gpt-6.1-terra / gpt-6.1-sol、Gemini 3.8 Flash / 4 Argon、GPT-OSS 120B。effort はすべて medium、各10回。
- 本番は `scripts/run_main.sh`（runs/main、ログは logs/run_main.log）。途中で止まっても同じコマンドで続きから再開できる。

## 本番実験の結果（2026-10-31 01:24〜05:06、70セル×10回、IK のやり直し0回）
集計は `python3 scripts/analyze.py --tag main --since 1793377453` で results/main_*.csv と results/main_summary.md に出る。
予備実験・正解コードは `--tag pilot|oracle --until 1793377453`。runs/oracle の noisy_avg は平均化コードの書き損じ（全試行で例外）なので使わない。正しいのは check_avg。

成功数/10:

| モデル | 積む | ナット | 積み替え | 受け渡し | 積み替え(複数) | 受け渡し(複数) | 誤差:積む | 誤差:ナット | 誤差複数:積む | 誤差複数:ナット |
|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5 | 10 | 6 | 0 | 3 | 1 | 3 | 7 | 0 | 5 | 2 |
| Opus 5.5 | 10 | 5 | 0 | 7 | 1 | 6 | 9 | 5 | 9 | 1 |
| gpt-6.1-terra | 9 | 7 | 0 | 0 | 0 | 2 | 7 | 6 | 4 | 8 |
| gpt-6.1-sol | 10 | 10 | 0 | 10 | 0 | 9 | 9 | 4 | 8 | 7 |
| Gemini 3.8 Flash | 10 | 9 | 0 | 7 | 0 | 10 | 7 | 1 | 9 | 2 |
| Gemini 4 Argon | 10 | 4 | 0 | 5 | 5 | 3 | 10 | 3 | 10 | 6 |
| GPT-OSS 120B | 9 | 5 | 0 | 0 | 0 | 0 | 8 | 1 | 6 | 1 |

分かったこと:
- 積むは全モデルほぼ満点で差が出ない。差が出るのは受け渡し（両腕の協調）とナット（向きの合わせ）。
- 1回で答える条件の総合は gpt-6.1-sol が最上位（受け渡し 10/10、ナット 10/10）。同じ会社の軽いモデル（terra）は受け渡し 0/10 で、軽量と上位の差は Codex が一番大きい。Claude と Gemini は軽いモデルでも上位と同等以上の課題がある。
- 積み替えは1回で答えると全モデル 0/10（初期状態で緑が赤の上に載っているのを確かめない）。複数ターンにすると Argon だけ 5/10 になり、その5回はすべて「実行結果を見て書き直した」試行。Flash と gpt-6.1-sol は一度も書き直さずに「完了」と答えるので、複数ターンの効果が出ない。
- 位置に 1cm の誤差を足すと、ナットが大きく下がるモデルが多い（Flash 9→1、Haiku 6→0）。積むは下がり幅が小さい。ただし誤差ありの条件は同じ設定で回し直しても1セルで最大5回ぶれる（下の点検を参照）ので、誤差ありの条件の細かい差や複数ターンの効果は、10回では言い切れない。
- コードが例外で落ちたのは Haiku の積み替え（1回で答える条件）5回だけ。`import numpy as np` を書き忘れた。ほかの失敗はすべて「コードは最後まで動いたが、物体が目標どおりにならなかった」もの。
- 呼び出しエラーは 1,089 回中 8 回（GPT-OSS 7、Argon 1）。いずれも CaP-X の再試行で回復した。所要時間の中央値は terra 6 秒、Flash 30 秒、ほかは 12〜15 秒。

## CLI の層の点検（2026-10-31 09:00〜）
疑い: (1) codex exec が個人ルール（~/.codex/AGENTS.md）を読んでいる、(2) Codex と agy が回答中にツールを使えた。
- (1) は起きていた。Codex は毎回、個人ルール・メモリ（User Profile）・スキル一覧・プラグインのフック・MCP（node_repl）を文脈に入れていた。「OK とだけ答えて」で入力 23,299 トークン。Claude は --system-prompt と --setting-sources "" で素の状態（自己申告でも何も無い）。agy は個人ルール・MCP・プラグインが無く、agy 本体の指示文とツール定義だけ。
- (2) は起きていなかった。agy は本番の 468 会話すべてが「入力 → 回答」の2段だけ（agy の会話記録の step_type で確認、ツールの段は0）。Codex は過去の記録が無いので、本番のプロンプト16件を同じ引数で --json 付きで流し直し、ツール呼び出し0回。
- 対策: proxy の既定を `--codex-home clean` にした。認証ファイルだけをリンクした専用の CODEX_HOME（~/.cache/pai-final/codex-home）を作り、組み込みの指示文を SYSTEM_PROMPT に置き換え（model_instructions_file）、メモリ・プラグイン・フック・ツールを切る。入力は 23,299 → 7,918 トークン（本番のプロンプトでは約 24,000 → 8,600）。残るのは Codex 本体の組み込みスキル一覧と、動かない状態のツール定義だけ。
- Codex の2モデルの全20セルを `scripts/run_clean.sh`（runs/clean）でやり直した（呼び出し 281 回、エラー0、IK の失敗0）。Claude と agy はやり直していない。
  集計: `python3 scripts/analyze.py --tag clean --since $(cat logs/clean_start.txt)` → results/clean_*。
- 結果: 誤差なしの6セルずつは、どちらのモデルも1セルあたり差が1回以内（sol の受け渡し 10→10、terra の受け渡し 0→1、sol のナット 10→9 など）。
  誤差ありのセルは上下どちらにもぶれた（sol 誤差ナット 4→8、terra 誤差複数ナット 8→3、terra 誤差積む 7→4）。どれも Fisher の正確検定で p>0.05。
  100試行の合計は sol 67→70、terra 43→37 で、向きもそろっていない。
- 判断: 個人ルールなどの混入で、Codex の成績が一方向にずれた形跡はない。モデルの順位（受け渡しは sol が最上位、terra が最下位近く）も変わらない。
  ただし条件をそろえた runs/clean を Codex の正式な値として使い、runs/main の Codex の値は点検の比較用として残す。
- 所要時間の中央値は短くなった（sol 11.7→8.9 秒、terra 6.1→4.6 秒）。入力が約1.5万トークン減ったぶん。

## 追加モデル（2026-10-31 午後）
- gpt-6-astra@medium を runs/clean で全10セル（`./scripts/run_clean.sh codex-cli/gpt-6-astra@medium`）。
  12:03〜12:59 に Codex の利用上限で呼び出しが44回失敗し、誤差あり・積むの trial 07〜09 が回答なしで失敗扱いになった。
  このセルは runs/invalid/clean_noisy_astra_usage_limit/ に移し、10回やり直した（呼び出し10回、エラー0）。ほかのセルは上限の前後で、全試行が回答あり。
  成功数/10: 積む 10、ナット 8、積み替え 0、受け渡し 10、積み替え(複数) 0、受け渡し(複数) 10、誤差:積む 4、誤差:ナット 8、誤差複数:積む 9、誤差複数:ナット 8。
- Fable（claude-fable-5-1@medium）はクラウドで実行（ブランチ fable-cloud、cloud_runs/ENV.md）。
  1回で答える6セルの回答60個は replay/ に作り、手元で `replay-cli/claude-fable-5-1@medium` として再生した（runs/clean、ログ logs/run_fable_replay.log）。
  再生は60回すべて別の回答（足りない・使い回し0）。各セルのプロンプトのハッシュは cells.json と一致。
  成功数/10（手元の Mac）: 積む 9、ナット 3、積み替え 0、受け渡し 0、誤差:積む 7、誤差:ナット 3。
  複数ターン4セル（クラウドの Linux、CPU 描画）: 積み替え 2、受け渡し 2、誤差複数:積む 7、誤差複数:ナット 1。正解コードの確認は4タスクとも 3/3。
  受け渡しは手元（1回）でもクラウド（複数）でも低いので、クラウドの環境のせいではなく Fable の書き方の問題と見られる。
  1回で答える受け渡しの失敗はすべて「コードは最後まで動いたが、持ち替えられなかった」もの。原因（腕1の向きの指定など）はまだ確かめていない。

## 案A の準備（2026-10-31 夕、ブランチ plana-colab）
Qwen3.5-9B を Colab の GPU（vLLM）で、stack・nut・handover × base/skill/base_mt/skill_mt × 各10回。GPU の要らない部分を作って試運転した。
- スキルライブラリ: `scripts/select_skills.py` → `skill_lib/<task>.md`。他タスクの成功コードを見本タスクごとに1件
  （sol → astra → Opus の順、base 優先、最短）。stack の見本に restack は入れない。理由は `skill_lib/README.md`。
- 注入: `scripts/make_configs.py` の skill・skill_mt が `env.cfg.prompt` を「既定のタスク文 + 見本」にする（CaP-X 本体は変えない）。
  `scripts/check_skill_prompts.py` で、見本を除くと base と1文字も違わないことを設定と実際の送信の両方で確認。
- CaP-X の変更を1つ追加（`patches/capx.patch`）: 環境変数 `CAPX_VIDEO_TRIALS` で動画を最初の N 試行だけにする。
  `run_grid.py --video-trials N`・`--server-url`、Linux では描画の既定を osmesa に。
- Colab: `colab/pai_planA.ipynb`（`colab/build_notebook.py` から生成）と `colab/README.md`。記録用の中継 `proxy/log_proxy.py`、
  試運転用のダミー `proxy/dummy_llm.py`、描画の確認 `colab/check_gl.py`、CaP-X の導入 `colab/setup_capx.sh`。
- vLLM: 0.31.0（CUDA 13）と 0.19.1（CUDA 12.8）の両方で、Qwen3.5 対応・`--language-model-only`・
  `--default-chat-template-kwargs '{"enable_thinking": false}'` を確認。ドライバーに合わせて選ぶ。
- 試運転（GPU なしのコンテナ、Hugging Face に届かないのでダミーのモデル）: 4条件×3タスク×1試行が通り、
  複数ターン（REGENERATE→FINISH）・見本の注入・集計を確認。oracle は3タスクとも 3/3。

## 案A の結果（2026-11-01、Colab の A100、本番は 12:11 に回収）
- 120 試行すべて完走（vLLM のエラー 0、見張りの合図 0）。環境と注意点は `runs/planA/ENV_planA.md`、表は `results/planA_summary.md`。
- そのまま 1/10・0/10・0/10（積む・ナット・受け渡し）。積むは ① 5/10、② 5/10、①＋② 6/10。ナット・受け渡しは ①② でもほぼ 0（60 試行で 1 回）。
  積むの差は1つずつだと Fisher で p=0.14・0.14・0.057 で言い切れないが、3条件まとめると 16/30 対 1/10 で p=0.026。
  「何かを足すと上がる」はほぼ言える（まとめ方は結果を見てから決めた）。①と②のどちらが効いたかは区別できない。
- ①の成功のうち、書き直さずに最初のコードで成功したのは 3/5（①＋② は 4/6）。書き直した試行が書き直して初めて成功したのかは、ターンごとの成否が残っていないので分からない。
- ①はコードが例外で止まるのを減らした（16/30 → 2/30）が、止まらなくなっても成功しない。小さいモデルは「最後まで動くコード」でまずつまずく。
- ②の副作用: 積むの見本にあるナット用の関数 `goto_home_joint_position`（積むの API には無い。見本には使える関数の一覧も付けていた）を
  4 試行が写して NameError（うち 2 は積み終えたあとなので成功）。①＋② で書き直して成功した 2 試行のうち 1 つはこれを直したもの（もう 1 つは SyntaxError）。
- 例外の内訳は `report/tables/casea_errors.csv`（1回で答える条件のみ。複数ターンは Colab から持ち帰ったフォルダの更新時刻がそろい、順番が分からない）。
- 集計の直し（2026-11-01 夜、Codex のレビューで発見）: Colab から zip で持ち帰ると試行のフォルダの更新時刻がそろうので、
  `analyze.py` が複数ターンの2試行（base_mt の積む trial 4・受け渡し trial 9）で途中経過のフォルダを最終として選んでいた。
  summary.txt に「Num Code Blocks」のある完了フォルダを優先するように直し、`results/planA_*` を集計し直した（成功数は変わらず、例外の数と書き直しの回数が変わった）。
  runs/main・runs/clean では、この直しで選ぶフォルダは変わらない。
- 2026-11-01 夜: plana-colab と report-draft（クラウドのレポート下書き）を main にマージし、`make_report.py` を `results/planA_*` に対応させ、レポート6章を書いた。

## 制約
- Mac で動くのは特権情報（シミュレータの真の位置）を使う設定だけ。画像認識の設定は SAM3 などの GPU が要る。
- オープンモデル（Qwen）は Colab の GPU で、CaP-X ごと動かす予定。

## 提出物（2026-11-01 夜）
- レポート PDF: `report/report_template.md` に要旨と GitHub の URL を足し、`report/build_pdf.py`（Chrome のヘッドレス印刷）で A4・13 ページにした。
- 動画（1分39秒、字幕のみ、1920×1080）: `scripts/make_video.py`。タイトル → やったこと → 全体の表 → 受け渡し（sol 成功・terra 失敗）
  → 積み替え（1回で失敗・Argon が書き直して成功）→ 位置の誤差（Haiku の積む。ナットは最後のコマで腕が柱を隠して成否が見えないので、数字だけ字幕に出す）
  → 平均化のコード（Opus）→ 案A（Qwen の積む）→ まとめ。
- PDF と動画は提出用の名前（アカウント名入り）なので、リポジトリの外に置いた。
- LICENSE（MIT）を追加。公開前に全ブランチの履歴を点検（作者はすべて pai-final、個人のパス・メール・キーは無し）。

## 次にやること
1. 動画を YouTube に上げる（限定公開以上）。
2. リポジトリを公開し、Omnicampus に提出する。

## 動かし方
```bash
# 中継サーバー
../third_party/cap-x/.venv-mac/bin/python proxy/cli_proxy.py --port 8120
# 1回試す（cap-x のフォルダで）
MUJOCO_GL=cgl CAPX_LLM_TIMEOUT=600 .venv-mac/bin/python capx/envs/launch.py \
  --config-path env_configs/cube_lifting/franka_robosuite_cube_lifting_privileged.yaml \
  --model claude-cli/claude-sonnet-5-5 --server-url http://127.0.0.1:8120/chat/completions \
  --total-trials 1 --num-workers 1 --record-video True --output-dir <出力先>
```
