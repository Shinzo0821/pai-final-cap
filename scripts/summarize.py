"""runs/<tag>/ 以下の launch.log をすべて読み、成功率の表を作る。

  python scripts/summarize.py --tag pilot

runs/<tag>/results.csv を書き出し、条件ごとに「モデル × タスク」の表を表示する。
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_grid import ROOT, count_results  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    run_root = ROOT / "runs" / args.tag
    rows = []
    for log in sorted(run_root.glob("*/*/*/launch.log")):
        out_dir = log.parent
        cond, model, task = out_dir.relative_to(run_root).parts
        ok, n = count_results(out_dir)
        rows.append({"cond": cond, "model": model.replace("__", "/"), "task": task, "success": ok, "trials": n})
    with (run_root / "results.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["cond", "model", "task", "success", "trials"])
        w.writeheader()
        w.writerows(rows)

    by_cond: dict[str, dict[str, dict[str, str]]] = defaultdict(lambda: defaultdict(dict))
    tasks: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        by_cond[r["cond"]][r["model"]][r["task"]] = f"{r['success']}/{r['trials']}"
        if r["task"] not in tasks[r["cond"]]:
            tasks[r["cond"]].append(r["task"])
    for cond, models in by_cond.items():
        print(f"\n[{cond}]")
        print(f"{'model':42s}" + "".join(f"{t:>10s}" for t in tasks[cond]))
        for model, cells in models.items():
            print(f"{model:42s}" + "".join(f"{cells.get(t, '-'):>10s}" for t in tasks[cond]))


if __name__ == "__main__":
    main()
