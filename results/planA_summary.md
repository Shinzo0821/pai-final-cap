# runs/planA の集計

## base（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | stack |
|---|---|---|---|
| qwen3.5-9b | 0/10 (7) | 0/10 (7) | 1/10 (2) |

## base_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | stack |
|---|---|---|---|
| qwen3.5-9b | 0/10 (0) | 0/10 (1) | 5/10 (1) |

## skill（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | stack |
|---|---|---|---|
| qwen3.5-9b | 0/10 (4) | 1/10 (4) | 5/10 (5) |

## skill_mt（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）

| model | handover | nut | stack |
|---|---|---|---|
| qwen3.5-9b | 0/10 (4) | 0/10 (2) | 6/10 (0) |

## LLM 呼び出し

| model | calls | errors | median latency (s) | mean response chars |
|---|---|---|---|---|
| qwen3.5-9b | 289 | 0 | 21.9 | 5811 |
