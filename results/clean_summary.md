# runs/clean の集計

## base（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | restack | stack |
|---|---|---|---|---|
| codex-cli/gpt-6-astra@medium | 10/10 (0) | 8/10 (0) | 0/10 (0) | 10/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 10/10 (0) | 9/10 (0) | 0/10 (0) | 10/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 1/10 (0) | 7/10 (0) | 0/10 (0) | 9/10 (0) |
| replay-cli/claude-fable-5-1@medium | 0/10 (0) | 3/10 (0) | 0/10 (0) | 9/10 (0) |

## base_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | restack |
|---|---|---|
| codex-cli/gpt-6-astra@medium | 10/10 (0) | 0/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 10/10 (0) | 0/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 2/10 (0) | 0/10 (0) |

## noisy（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | nut | stack |
|---|---|---|
| codex-cli/gpt-6-astra@medium | 8/10 (0) | 4/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 8/10 (0) | 8/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 8/10 (0) | 4/10 (0) |
| replay-cli/claude-fable-5-1@medium | 3/10 (0) | 7/10 (0) |

## noisy_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | nut | stack |
|---|---|---|
| codex-cli/gpt-6-astra@medium | 8/10 (0) | 9/10 (0) |
| codex-cli/gpt-6.1-sol@medium | 9/10 (0) | 6/10 (0) |
| codex-cli/gpt-6.1-terra@medium | 3/10 (0) | 3/10 (0) |

## LLM 呼び出し

| model | calls | errors | median latency (s) | mean response chars |
|---|---|---|---|---|
| codex-cli/gpt-6-astra@medium | 192 | 44 | 8.1 | 1160 |
| codex-cli/gpt-6.1-sol@medium | 140 | 0 | 8.9 | 1185 |
| codex-cli/gpt-6.1-terra@medium | 141 | 0 | 4.6 | 787 |
| replay-cli/claude-fable-5-1@medium | 84 | 0 | 0.0 | 1138 |
