"""本番実験（runs/<tag>）の試行ごとの記録と LLM 呼び出しの記録をまとめ、results/ に書き出す。

  python scripts/analyze.py --tag main --since 1793377453

書き出すもの（results/<tag>_*.csv と results/<tag>_summary.md）:
- trials.csv: 1試行1行。コードが例外で落ちたか、報酬、成功、コードブロック数、作り直し回数。
- cells.csv:  条件×モデル×タスクごとの成功数、コードが落ちた数、平均コードブロック数。
- calls.csv:  モデルごとの呼び出し回数、エラー数、所要時間の中央値、出力の長さ。
--since / --until（UNIX 時刻）の外の呼び出しは数えない（別の実験の分を除くため）。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRIAL_RE = re.compile(r"trial_(\d+)_sandboxrc_(-?\d+)_reward_([-\d.]+)_taskcompleted_(\d)")
SUMMARY_RE = {
    "regenerations": re.compile(r"Num Regenerations: (\d+)"),
    "code_blocks": re.compile(r"Num Code Blocks: (\d+)"),
}


def final_trial_dirs(run_root: Path) -> list[Path]:
    """複数ターンでは同じ試行番号の途中経過フォルダも残るので、最後に書かれたものだけを返す。"""
    latest: dict[tuple, Path] = {}
    for d in run_root.glob("*/*/*/*/trial_*"):
        m = TRIAL_RE.fullmatch(d.name)
        if not m:
            continue
        key = (d.parent, int(m.group(1)))
        if key not in latest or d.stat().st_mtime > latest[key].stat().st_mtime:
            latest[key] = d
    return sorted(latest.values())


def read_trials(run_root: Path) -> list[dict]:
    rows = []
    for d in final_trial_dirs(run_root):
        m = TRIAL_RE.fullmatch(d.name)
        cond, model_dir, _, task = d.relative_to(run_root).parts[:4]
        row = {
            "cond": cond,
            "model": model_dir.replace("__", "/"),
            "task": task,
            "trial": int(m.group(1)),
            "code_failed": int(m.group(2) != "0"),
            "reward": float(m.group(3)),
            "success": int(m.group(4)),
            "code_blocks": "",
            "regenerations": "",
        }
        summary = d / "summary.txt"
        if summary.exists():
            text = summary.read_text(errors="replace")
            for key, pat in SUMMARY_RE.items():
                found = pat.findall(text)
                if found:
                    row[key] = int(found[-1])
        rows.append(row)
    return rows


def cell_table(trials: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for t in trials:
        groups[(t["cond"], t["model"], t["task"])].append(t)
    out = []
    for (cond, model, task), ts in sorted(groups.items()):
        blocks = [t["code_blocks"] for t in ts if t["code_blocks"] != ""]
        out.append({
            "cond": cond,
            "model": model,
            "task": task,
            "trials": len(ts),
            "success": sum(t["success"] for t in ts),
            "code_failed": sum(t["code_failed"] for t in ts),
            "mean_code_blocks": round(statistics.mean(blocks), 2) if blocks else "",
        })
    return out


def call_table(log_path: Path, since: float, until: float, models: set[str]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for line in log_path.read_text().splitlines():
        rec = json.loads(line)
        if not since <= rec["time"] < until or rec["model"] not in models:
            continue
        groups[rec["model"]].append(rec)
    out = []
    for model, recs in sorted(groups.items()):
        ok = [r for r in recs if r["status"] == "ok"]
        out_tok = [r["output_tokens"] for r in ok if r.get("output_tokens")]
        out.append({
            "model": model,
            "calls": len(recs),
            "errors": len(recs) - len(ok),
            "median_latency_s": round(statistics.median(r["latency_s"] for r in ok), 1) if ok else "",
            "mean_response_chars": round(statistics.mean(r["response_chars"] for r in ok)) if ok else "",
            "mean_output_tokens": round(statistics.mean(out_tok)) if out_tok else "",
        })
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.unlink(missing_ok=True)
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


COND_ORDER = ["base", "base_mt", "noisy", "noisy_mt"]


def markdown(tag: str, cells: list[dict], calls: list[dict]) -> str:
    lines = [f"# runs/{tag} の集計", ""]
    conds = sorted({c["cond"] for c in cells}, key=lambda c: (COND_ORDER.index(c) if c in COND_ORDER else 99, c))
    for cond in conds:
        cs = [c for c in cells if c["cond"] == cond]
        tasks = sorted({c["task"] for c in cs})
        models = sorted({c["model"] for c in cs})
        lines += [f"## {cond}（成功数/試行数、括弧内はコードが例外で落ちた数、– は未実施）", ""]
        lines.append("| model | " + " | ".join(tasks) + " |")
        lines.append("|---|" + "---|" * len(tasks))
        for m in models:
            vals = []
            for t in tasks:
                c = next((x for x in cs if x["model"] == m and x["task"] == t), None)
                vals.append(f"{c['success']}/{c['trials']} ({c['code_failed']})" if c else "–")
            lines.append(f"| {m} | " + " | ".join(vals) + " |")
        lines.append("")
    if not calls:
        return "\n".join(lines) + "\n"
    lines += ["## LLM 呼び出し", "", "| model | calls | errors | median latency (s) | mean response chars |", "|---|---|---|---|---|"]
    for c in calls:
        lines.append(f"| {c['model']} | {c['calls']} | {c['errors']} | {c['median_latency_s']} | {c['mean_response_chars']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--since", type=float, default=0.0, help="これより前の呼び出しは数えない（UNIX 時刻）")
    ap.add_argument("--until", type=float, default=float("inf"), help="これ以降の呼び出しは数えない（UNIX 時刻）")
    args = ap.parse_args()
    run_root = ROOT / "runs" / args.tag
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)

    trials = read_trials(run_root)
    cells = cell_table(trials)
    calls = call_table(ROOT / "logs" / "proxy_calls.jsonl", args.since, args.until, {c["model"] for c in cells})
    write_csv(out_dir / f"{args.tag}_trials.csv", trials)
    write_csv(out_dir / f"{args.tag}_cells.csv", cells)
    write_csv(out_dir / f"{args.tag}_calls.csv", calls)
    (out_dir / f"{args.tag}_summary.md").write_text(markdown(args.tag, cells, calls))
    print(markdown(args.tag, cells, calls))


if __name__ == "__main__":
    main()
