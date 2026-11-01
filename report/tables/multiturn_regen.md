| モデル | タスク | 書き直した試行 | 成功のうち書き直した試行 |
|---|---|---|---|
| Claude Haiku 5.5 | 積み替え | 5/10 | 1/1 |
| Claude Haiku 5.5 | 受け渡し | 8/10 | 2/3 |
| Claude Opus 5.5 | 積み替え | 1/10 | 1/1 |
| Claude Opus 5.5 | 受け渡し | 3/10 | 2/6 |
| gpt-6.1-terra | 積み替え | 0/10 | 0/0 |
| gpt-6.1-terra | 受け渡し | 0/10 | 0/2 |
| gpt-6.1-sol | 積み替え | 0/10 | 0/0 |
| gpt-6.1-sol | 受け渡し | 0/10 | 0/10 |
| gpt-6-astra | 積み替え | 0/10 | 0/0 |
| gpt-6-astra | 受け渡し | 0/10 | 0/10 |
| Gemini 3.8 Flash | 積み替え | 0/10 | 0/0 |
| Gemini 3.8 Flash | 受け渡し | 0/10 | 0/10 |
| Gemini 4 Argon | 積み替え | 5/10 | 5/5 |
| Gemini 4 Argon | 受け渡し | 2/10 | 0/3 |
| GPT-OSS 120B | 積み替え | 2/10 | 0/0 |
| GPT-OSS 120B | 受け渡し | 3/10 | 0/0 |

複数ターン（誤差なし）。コードブロックが2個以上の試行を「書き直した」とした（results/*_trials.csv の code_blocks）。Fable はクラウドの実行で trials.csv が無いので除いた。
