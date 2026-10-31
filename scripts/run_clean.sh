#!/bin/zsh
# Codex だけを、個人ルールやメモリを外した CODEX_HOME（proxy の --codex-home clean）でやり直す。
# 条件とタスクは run_main.sh と同じ。結果は runs/clean に出し、runs/main と比べる。
# 事前に proxy/cli_proxy.py（8120、既定の --codex-home clean）を起動しておく。
set -u
cd "$(dirname "$0")/.."
PY=../third_party/cap-x/.venv-mac/bin/python
# 引数でモデルを指定できる（例: ./scripts/run_clean.sh codex-cli/gpt-6-astra@medium）
if (( $# > 0 )); then
  MODELS=("$@")
else
  MODELS=(
    codex-cli/gpt-6.1-terra@medium
    codex-cli/gpt-6.1-sol@medium
  )
fi
run() { $PY scripts/run_grid.py --tag clean --models $MODELS --trials 10 --workers 3 --video "$@"; }

run --conds base --tasks stack restack nut handover
run --conds base_mt --tasks restack handover
run --conds noisy --tasks stack nut
run --conds noisy_mt --tasks stack nut
echo "ALL DONE"
