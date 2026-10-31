"""スキルライブラリの注入を確かめる。

1. 設定（いつでも）: configs/skill/<task>.yaml と公式の設定（base）、configs/skill_mt と configs/base_mt を比べ、
   - env.cfg.prompt と output_dir 以外がまったく同じこと
   - env.cfg.prompt が「既定のタスク文 + "\\n" + skill_lib/<task>.md」であること
   - その既定のタスク文が、これまでの実験でモデルが実際に見たプロンプト（skill_src/prompts）の先頭と同じで、
     その直後が "\\nAPIs:\\n" であること（= 見本の部分を除けば base と1文字も変わらない）
2. 実行結果（--run runs/<tag> を付けたとき）: CaP-X が書いた initial_prompt.txt を条件ごとに比べ、
   skill から見本の部分を除くと base と完全に一致すること（skill_mt と base_mt も）。
3. 呼び出しの記録（--calls を付けたとき）: 送られたプロンプトのうち、見本を含むもの・複数ターンの判断のもの・
   応答に <think> があったものの数。

  python3 scripts/check_skill_prompts.py [--run runs/planA] [--calls logs/llm_calls.jsonl]
終了コード: 食い違いがあれば 1。
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_grid import CAPX, TASKS  # noqa: E402

SKILL_TASKS = ("stack", "nut", "handover")
PAIRS = (("skill", "base"), ("skill_mt", "base_mt"))
BASE_PROMPT_FILE = {"stack": "base_stack.txt", "nut": "base_nut.txt", "handover": "base_handover.txt"}
SKILL_MARK = "Reference examples (skill library):"
MT_MARK = "The following code blocks were just executed"


def load_cfg(cond: str, task: str) -> dict:
    path = CAPX / TASKS[task] if cond == "base" else ROOT / "configs" / cond / f"{task}.yaml"
    return yaml.safe_load(path.read_text())


def strip(cfg: dict) -> dict:
    cfg = json.loads(json.dumps(cfg))
    cfg["env"]["cfg"].pop("prompt", None)
    cfg.pop("output_dir", None)
    return cfg


def user_text(prompt_repr: str) -> str:
    msgs = ast.literal_eval(prompt_repr)
    return "".join(p.get("text", "") for p in msgs[-1]["content"] if isinstance(p, dict))


def check_configs() -> list[str]:
    errors = []
    for task in SKILL_TASKS:
        skill_md = (ROOT / "skill_lib" / f"{task}.md").read_text()
        seen = user_text((ROOT / "skill_src" / "prompts" / BASE_PROMPT_FILE[task]).read_text())
        for skill_cond, base_cond in PAIRS:
            s, b = load_cfg(skill_cond, task), load_cfg(base_cond, task)
            if strip(s) != strip(b):
                errors.append(f"{skill_cond}/{task}: settings other than the prompt differ from {base_cond}")
            if "prompt" in b["env"]["cfg"]:
                errors.append(f"{base_cond}/{task}: base config unexpectedly overrides the prompt")
            prompt = s["env"]["cfg"].get("prompt", "")
            if not prompt.endswith("\n" + skill_md):
                errors.append(f"{skill_cond}/{task}: prompt does not end with skill_lib/{task}.md")
                continue
            default = prompt[: -len("\n" + skill_md)]
            if not seen.startswith(default + "\nAPIs:\n"):
                errors.append(f"{skill_cond}/{task}: default task text differs from the prompt seen in earlier runs")
            print(f"  ok config  {skill_cond:8s} vs {base_cond:7s} {task:9s} "
                  f"(task text {len(default)} chars + skill {len(skill_md)} chars)")
    return errors


def find_prompt(run: Path, cond: str, task: str) -> Path | None:
    found = sorted(run.glob(f"{cond}/*/*/{task}/initial_prompt.txt"))
    return found[-1] if found else None


def check_run(run: Path) -> list[str]:
    errors = []
    for task in SKILL_TASKS:
        skill_md = (ROOT / "skill_lib" / f"{task}.md").read_text()
        for skill_cond, base_cond in PAIRS:
            ps, pb = find_prompt(run, skill_cond, task), find_prompt(run, base_cond, task)
            if not ps or not pb:
                print(f"  --  run    {skill_cond:8s} vs {base_cond:7s} {task:9s} (initial_prompt.txt missing)")
                continue
            ts, tb = user_text(ps.read_text()), user_text(pb.read_text())
            if SKILL_MARK not in ts or skill_md not in ts:
                errors.append(f"run {skill_cond}/{task}: skill text not found in the sent prompt")
                continue
            if SKILL_MARK in tb:
                errors.append(f"run {base_cond}/{task}: base prompt contains the skill text")
            if ts.replace("\n" + skill_md, "", 1) != tb:
                errors.append(f"run {skill_cond}/{task}: prompt minus skill text != {base_cond} prompt")
                continue
            print(f"  ok run     {skill_cond:8s} vs {base_cond:7s} {task:9s} "
                  f"(identical except the {len(skill_md)}-char skill block; total {len(ts)} vs {len(tb)} chars)")
    return errors


def report_calls(path: Path, since: float) -> None:
    n = skill = mt = think = err = 0
    longest = 0
    for line in path.read_text().splitlines():
        r = json.loads(line)
        if r.get("time", 0) < since:
            continue
        text = "\n".join(
            (m["content"] if isinstance(m.get("content"), str)
             else "".join(p.get("text", "") for p in m.get("content", []) if isinstance(p, dict)))
            for m in r.get("messages") or []
        )
        n += 1
        skill += SKILL_MARK in text
        mt += MT_MARK in text
        think += bool(r.get("has_think_tag"))
        err += r.get("status") != "ok"
        longest = max(longest, r.get("input_tokens") or 0)
    print(f"  calls: {n} (with skill text {skill}, multi-turn decisions {mt}, <think> in reply {think}, "
          f"errors {err}, max prompt tokens {longest})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, help="runs/<tag>（CaP-X の出力）")
    ap.add_argument("--calls", type=Path, help="proxy/log_proxy.py の記録")
    ap.add_argument("--since", type=float, default=0.0)
    args = ap.parse_args()
    errors = check_configs()
    if args.run:
        errors += check_run(args.run)
    if args.calls and args.calls.exists():
        report_calls(args.calls, args.since)
    for e in errors:
        print("  NG", e)
    print("all checks passed" if not errors else f"{len(errors)} problem(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
