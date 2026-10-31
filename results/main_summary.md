# runs/main の集計

## base（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | restack | stack |
|---|---|---|---|---|
| agy-cli/gemini-3.8-flash-medium | 7/10 (0) | 9/10 (0) | 0/10 (0) | 10/10 (0) |
| agy-cli/gemini-4-argon-medium | 5/10 (0) | 4/10 (0) | 0/10 (0) | 10/10 (0) |
| agy-cli/gpt-oss-120b-medium | 0/10 (0) | 5/10 (0) | 0/10 (0) | 9/10 (0) |
| claude-cli/claude-haiku-5-5@medium | 3/10 (0) | 6/10 (0) | 0/10 (5) | 10/10 (0) |
| claude-cli/claude-opus-5-5@medium | 7/10 (0) | 5/10 (0) | 0/10 (0) | 10/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 10/10 (0) | 10/10 (0) | 0/10 (0) | 10/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 0/10 (0) | 7/10 (0) | 0/10 (0) | 9/10 (0) |

## base_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | restack |
|---|---|---|
| agy-cli/gemini-3.8-flash-medium | 10/10 (0) | 0/10 (0) |
| agy-cli/gemini-4-argon-medium | 3/10 (0) | 5/10 (0) |
| agy-cli/gpt-oss-120b-medium | 0/10 (0) | 0/10 (0) |
| claude-cli/claude-haiku-5-5@medium | 3/10 (0) | 1/10 (0) |
| claude-cli/claude-opus-5-5@medium | 6/10 (0) | 1/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 9/10 (0) | 0/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 2/10 (0) | 0/10 (0) |

## noisy（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | nut | stack |
|---|---|---|
| agy-cli/gemini-3.8-flash-medium | 1/10 (0) | 7/10 (0) |
| agy-cli/gemini-4-argon-medium | 3/10 (0) | 10/10 (0) |
| agy-cli/gpt-oss-120b-medium | 1/10 (0) | 8/10 (0) |
| claude-cli/claude-haiku-5-5@medium | 0/10 (0) | 7/10 (0) |
| claude-cli/claude-opus-5-5@medium | 5/10 (0) | 9/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 4/10 (0) | 9/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 6/10 (0) | 7/10 (0) |

## noisy_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | nut | stack |
|---|---|---|
| agy-cli/gemini-3.8-flash-medium | 2/10 (0) | 9/10 (0) |
| agy-cli/gemini-4-argon-medium | 6/10 (0) | 10/10 (0) |
| agy-cli/gpt-oss-120b-medium | 1/10 (0) | 6/10 (0) |
| claude-cli/claude-haiku-5-5@medium | 2/10 (0) | 5/10 (0) |
| claude-cli/claude-opus-5-5@medium | 1/10 (0) | 9/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 7/10 (0) | 8/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 8/10 (0) | 4/10 (0) |

## LLM 呼び出し

| model | calls | errors | median latency (s) | mean response chars |
|---|---|---|---|---|
| agy-cli/gemini-3.8-flash-medium | 140 | 0 | 29.5 | 1226 |
| agy-cli/gemini-4-argon-medium | 172 | 1 | 15.2 | 2162 |
| agy-cli/gpt-oss-120b-medium | 156 | 7 | 11.9 | 1569 |
| claude-cli/claude-haiku-5-5@medium | 177 | 0 | 12.8 | 1663 |
| claude-cli/claude-opus-5-5@medium | 153 | 0 | 12.4 | 1608 |
| codex-cli/gpt-6.1-sol@medium | 140 | 0 | 11.7 | 1327 |
| codex-cli/gpt-6.1-terra@medium | 151 | 0 | 6.1 | 815 |
