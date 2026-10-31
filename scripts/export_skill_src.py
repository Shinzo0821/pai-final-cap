"""スキルライブラリの材料（大きいモデルの成功コード）を runs/ から skill_src/ に書き出す。

対象は誤差なしの条件（base・base_mt）で task_completed=1 の試行の code.py。
出どころは results/all_summary.md の正式な値と同じにする:
  - runs/main  : Claude（Haiku・Opus）・Gemini・GPT-OSS（Codex は runs/clean が正式なので除く）
  - runs/clean : Codex（terra・sol・astra）・Fable の1回で答える条件（replay）
  - cloud_runs/cloud : Fable の複数ターン（モデルの階層が無い）
複数ターンの code.py は「# Code block N」で区切られた全ブロック（最後のブロックが完了時のコード）。

使い方: python3 scripts/export_skill_src.py
出力:   skill_src/<task>/<cond>__<model>__trial_XX.py、skill_src/index.csv、skill_src/prompts/<cond>_<task>.txt
"""

from __future__ import annotations

import csv
import hashlib
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "skill_src"
TASKS = ("stack", "nut", "restack", "handover")
CONDS = ("base", "base_mt")
FABLE_CLOUD_MODEL = "claude-cli__claude-fable-5-1@medium"


def trials():
    """(source, cond, model, task, trial_dir) を返す。"""
    for src in ("main", "clean"):
        for cond in CONDS:
            for model_dir in sorted((ROOT / "runs" / src / cond).glob("*/")):
                model = model_dir.name
                if src == "main" and model.startswith("codex-cli__"):
                    continue
                for task in TASKS:
                    for t in sorted(model_dir.glob(f"*/{task}/trial_*_taskcompleted_1")):
                        yield src, cond, model, task, t
    for cond in CONDS:
        for task in TASKS:
            for t in sorted((ROOT / "cloud_runs" / "cloud" / cond / task).glob("trial_*_taskcompleted_1")):
                yield "cloud", cond, FABLE_CLOUD_MODEL, task, t


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    rows = []
    prompts_done: set[tuple[str, str]] = set()
    for src, cond, model, task, t in trials():
        code_path = t / "code.py"
        if not code_path.exists():
            continue
        code = code_path.read_text()
        trial = re.match(r"trial_(\d+)", t.name).group(1)
        name = f"{cond}__{model}__trial_{trial}.py"
        dest = OUT / task / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code)
        rows.append({
            "task": task,
            "cond": cond,
            "model": model,
            "source": src,
            "trial": trial,
            "n_blocks": max(1, len(re.findall(r"^# Code block \d+", code, flags=re.M))),
            "n_lines": code.count("\n") + 1,
            "bytes": len(code.encode()),
            "sha1": hashlib.sha1(code.encode()).hexdigest()[:12],
            "file": str(dest.relative_to(OUT)),
            "orig": str(t.relative_to(ROOT)),
        })
        # 各条件・タスクのプロンプト（モデルが見た最初の指示）を1つだけ残す
        if (cond, task) not in prompts_done:
            p = t.parent / "initial_prompt.txt"
            if p.exists():
                (OUT / "prompts").mkdir(parents=True, exist_ok=True)
                shutil.copy(p, OUT / "prompts" / f"{cond}_{task}.txt")
                prompts_done.add((cond, task))

    with open(OUT / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} files -> {OUT.relative_to(ROOT)}")
    counts: dict[tuple[str, str], int] = {}
    for r in rows:
        counts[(r["task"], r["cond"])] = counts.get((r["task"], r["cond"]), 0) + 1
    for k in sorted(counts):
        print(*k, counts[k])
    dup = len(rows) - len({r["sha1"] for r in rows})
    print(f"同じ中身のファイル: {dup}")


if __name__ == "__main__":
    main()
