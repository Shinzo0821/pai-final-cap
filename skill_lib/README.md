# スキルライブラリ（案A の skill・skill_mt 条件）

小さいモデル（Qwen3.5-9B）に、大きいモデルが**別のタスク**で成功したコードを見本として見せる。
見本は `skill_src/`（`scripts/export_skill_src.py` が書き出した成功コード 243 個）から
`scripts/select_skills.py` で選び、タスクごとに `skill_lib/<task>.md` に書き出す。
この文面がそのままプロンプトに入る（入れ方は下の「注入のしかた」）。

## どのタスクの見本を使うか（leave-one-task-out）

| 対象タスク | 見本にするタスク | 理由 |
|---|---|---|
| stack | nut・handover | 自分自身（stack）は除く。restack（積み替え）は「赤を緑に積む」手順そのものを含むので除く |
| nut | stack・restack・handover | 自分以外はすべて使ってよい |
| handover | stack・restack・nut | 同上 |

## 選び方

1. **見本にするタスクごとに1件**（`--per-task` で変えられる）。
   - 小さいモデルは長い文脈で注意が散りやすい。複数ターンでは毎回「最初のプロンプト全体 + 実行したコード + 出力」を
     送り直すので、最初のプロンプトは短い方がよい。
   - 1件ずつでプロンプト全体は約 2,500〜3,500 トークン（目安。下の表）。2件ずつにすると約 4,000〜4,600 トークンで、
     どちらも 8k の目安には収まるが、件数を増やしても見せる型（パターン）はほとんど増えない。
2. **モデルの優先順**: gpt-6.1-sol → gpt-6-astra → Claude Opus 5.5 → 残りは `results/all_summary.md` の合計の順。
   - sol（合計 70/100）と astra（67/100）は全体の上位2つ。Opus は別の会社のモデルで、受け渡しなどで強い。
   - restack は sol・astra の成功が0回（1回で答える条件は全モデル 0/10）なので、自然に Opus の成功コードが選ばれる。
3. **1回で答えた条件（base）のコードを優先**し、無ければ複数ターン（base_mt）。1回で通ったコードは手順が完結している。
4. **その中で一番短いもの**（バイト数。同じなら試行番号が小さい方。同じ中身は1つと数える）。
   選ばれたものは目で読み、コメントがあって読みやすいことを確かめた。
5. **複数ターンのコード**は、最後のブロックが単独で動く（前のブロックの変数を使わない）なら最後のブロックだけ、
   そうでなければ全ブロック。restack の Opus（3ブロック）の3ブロック目は、状態を読み直し、
   つかめたかを確かめて最大4回やり直す完結したコードなので、それだけを使う
   （1ブロック目は最初の試み、2ブロック目は確認の print だけ）。

## 見本の見せ方

- 前置き（英語）で「これは**他のタスク**で成功したコードで、今のタスクの答えではない」「型を使い回してよい」
  「**今のタスクの API だけを呼ぶ**こと」を伝える。
- 各見本に、そのタスクの名前・Goal・そのタスクの API 名を添える（handover は腕が2本で API の名前が違うため）。
- どのモデルが書いたかはプロンプトに出さない（`selection.csv` にだけ記録）。
- コードは ```python のかこみで見せる。CaP-X は応答の中の最初の ```python から最後の ``` までを取り出すので、
  モデルが囲みを付けても付けなくても動く。

## 注入のしかた（CaP-X 本体は変えない）

CaP-X はプロンプトを「タスク文 + `\nAPIs:\n` + API の説明」で作り、タスク文は設定の `env.cfg.prompt`（無ければ
クラスの既定の `PROMPT`）から取る。`scripts/make_configs.py` の skill・skill_mt では、
`env.cfg.prompt` を「既定の `PROMPT` + `\n` + `skill_lib/<task>.md`」にする。見本はタスク文の後ろ、API の説明の前に入る。

確かめ方: `python3 scripts/check_skill_prompts.py [--run runs/planA]`
- 設定: skill と base（公式の設定）、skill_mt と base_mt で、`env.cfg.prompt` と `output_dir` 以外がまったく同じ。
- 文面: 見本の部分を除いたタスク文が、これまでの実験でモデルが実際に見たプロンプト（`skill_src/prompts`）と1文字も違わない。
- 実行結果: CaP-X が書いた `initial_prompt.txt` で、skill から見本の部分を除くと base と完全に一致する（試運転で確認済み）。

## 選ばれた見本（`selection.csv`）

| 対象 | 見本のタスク | ファイル（`skill_src/` から） | 使った部分 | 行数 |
|---|---|---|---|---|
| stack | nut | `nut/base__codex-cli__gpt-6.1-sol@medium__trial_01.py` | 全体 | 38 |
| stack | handover | `handover/base__codex-cli__gpt-6.1-sol@medium__trial_05.py` | 全体 | 72 |
| nut | stack | `stack/base__codex-cli__gpt-6.1-sol@medium__trial_05.py` | 全体 | 20 |
| nut | restack | `restack/base_mt__claude-cli__claude-opus-5-5@medium__trial_09.py` | 3ブロック目 | 76 |
| nut | handover | `handover/base__codex-cli__gpt-6.1-sol@medium__trial_05.py` | 全体 | 72 |
| handover | stack | `stack/base__codex-cli__gpt-6.1-sol@medium__trial_05.py` | 全体 | 20 |
| handover | restack | `restack/base_mt__claude-cli__claude-opus-5-5@medium__trial_09.py` | 3ブロック目 | 76 |
| handover | nut | `nut/base__codex-cli__gpt-6.1-sol@medium__trial_01.py` | 全体 | 38 |

## 長さ

| 対象 | 見本の文字数 | 見本のトークン（目安） | プロンプト全体（目安） |
|---|---|---|---|
| stack | 5,088 | 約 1,600 | 約 2,500 |
| nut | 7,607 | 約 2,400 | 約 3,300 |
| handover | 6,336 | 約 2,000 | 約 3,500 |

トークンは「英語とコードで 1 トークン ≈ 3.2 文字」の目安（この環境からは Hugging Face に届かず、
Qwen のトークナイザーで数えられなかった）。Colab では `logs/llm_calls.jsonl` の `input_tokens` に実際の数が残る。

## 作り直すとき

```bash
python3 scripts/select_skills.py
```

```bash
CAPX_PYTHON=../third_party/cap-x/.venv/bin/python python3 scripts/make_configs.py
```

```bash
python3 scripts/check_skill_prompts.py
```
