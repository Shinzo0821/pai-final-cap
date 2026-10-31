# runs/pilot の集計

## base（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | restack | stack | wipe |
|---|---|---|---|---|---|
| agy-cli/gemini-3.8-flash-low | 0/3 (0) | 3/3 (0) | 0/3 (0) | 3/3 (0) | 3/3 (0) |
| agy-cli/gemini-4-argon-medium | 1/3 (0) | – | 0/3 (0) | – | – |
| agy-cli/gpt-oss-120b-medium | 0/3 (0) | 3/3 (0) | 0/3 (0) | 3/3 (0) | 3/3 (0) |
| claude-cli/claude-haiku-5-5 | 1/3 (0) | 3/3 (0) | 0/3 (1) | 2/3 (0) | 2/3 (1) |
| claude-cli/claude-opus-5-5 | 2/3 (0) | – | 0/3 (0) | – | – |
| codex-cli/gpt-5.6-sol@low | 1/3 (0) | 3/3 (0) | 0/3 (0) | 3/3 (0) | 3/3 (0) |
| codex-cli/gpt-6-sol@medium | 2/3 (0) | – | 0/3 (0) | – | – |

## noisy（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | stack |
|---|---|
| agy-cli/gemini-4-argon-medium | 3/3 (0) |
| claude-cli/claude-haiku-5-5 | 3/3 (0) |
| claude-cli/claude-opus-5-5 | 3/3 (0) |
| codex-cli/gpt-6-sol@medium | 2/3 (0) |

## LLM 呼び出し

| model | calls | errors | median latency (s) | mean response chars |
|---|---|---|---|---|
| agy-cli/gemini-3.8-flash-low | 21 | 0 | 12.3 | 2022 |
| agy-cli/gemini-4-argon-medium | 10 | 0 | 17.2 | 2037 |
| agy-cli/gpt-oss-120b-medium | 36 | 4 | 13.0 | 1727 |
| claude-cli/claude-haiku-5-5 | 19 | 0 | 12.7 | 1777 |
| claude-cli/claude-opus-5-5 | 9 | 0 | 17.0 | 2190 |
| codex-cli/gpt-5.6-sol@low | 30 | 0 | 8.2 | 1154 |
| codex-cli/gpt-6-sol@medium | 9 | 0 | 13.7 | 1082 |
