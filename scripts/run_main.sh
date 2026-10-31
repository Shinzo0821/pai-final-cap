#!/bin/zsh
# 本番実験（7モデル × 各10回）。段階ごとに流し、途中で止まっても続きから再開できる。
# 事前に proxy/cli_proxy.py（8120）を起動しておく。IK サーバーは run_grid.py が面倒を見る。
set -u
cd "$(dirname "$0")/.."
PY=../third_party/cap-x/.venv-mac/bin/python
MODELS=(
  claude-cli/claude-haiku-5-5@medium
  claude-cli/claude-opus-5-5@medium
  codex-cli/gpt-6.1-terra@medium
  codex-cli/gpt-6.1-sol@medium
  agy-cli/gemini-3.8-flash-medium
  agy-cli/gemini-4-argon-medium
  agy-cli/gpt-oss-120b-medium
)
run() { $PY scripts/run_grid.py --tag main --models $MODELS --trials 10 --workers 3 --video "$@"; }

# 1. 公式のまま・1回で答える
run --conds base --tasks stack restack nut handover
# 2. 実行結果を見て直せる複数ターン（初期状態を確かめる必要がある課題）
run --conds base_mt --tasks restack handover
# 3. 位置に誤差・1回で答える（精度が要る課題）
run --conds noisy --tasks stack nut
# 4. 位置に誤差・複数ターン
run --conds noisy_mt --tasks stack nut
echo "ALL DONE"
