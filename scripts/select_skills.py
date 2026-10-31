"""スキルライブラリ（他タスクの成功コードの見本）を選び、skill_lib/<task>.md に書き出す。

材料: skill_src/（scripts/export_skill_src.py が書き出した大きいモデルの成功コード）
対象: stack・nut・handover。見本は「そのタスク以外」から選ぶ（leave-one-task-out）。
      ただし restack は stack を手順として含むので、stack の見本に restack は入れない。

選び方（理由は skill_lib/README.md）:
  1. 見本にするタスク（SOURCES）ごとに PER_TASK 件（既定 1 件）。
  2. モデルの優先順（MODEL_PRIORITY）で、そのタスクに成功コードがある最初のモデルを使う。
  3. 1回で答える条件（base）を優先し、無ければ複数ターン（base_mt）。
  4. その中で一番短いもの（バイト数、同じなら試行番号の小さい方）。同じ中身（sha1）は1つと数える。
  5. 複数ターンのコードは、最後のブロックが単独で動く（未定義の名前を使わない）なら最後のブロックだけ、
     そうでなければ全ブロック。

使い方: python3 scripts/select_skills.py [--per-task 1]
出力:   skill_lib/<task>.md（プロンプトにそのまま足す文面）、skill_lib/selection.csv（選んだファイル）
"""

from __future__ import annotations

import argparse
import ast
import builtins
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skill_src"
OUT = ROOT / "skill_lib"

TARGETS = ("stack", "nut", "handover")
# 対象タスク -> 見本にしてよいタスク
SOURCES = {
    "stack": ("nut", "handover"),            # restack は stack を含むので除く
    "nut": ("stack", "restack", "handover"),
    "handover": ("stack", "restack", "nut"),
}
# 上位の2つ（results/all_summary.md の合計 70・67）と、別の会社の Opus を先に。残りは合計の順。
MODEL_PRIORITY = (
    "codex-cli__gpt-6.1-sol@medium",
    "codex-cli__gpt-6-astra@medium",
    "claude-cli__claude-opus-5-5@medium",
    "agy-cli__gemini-4-argon-medium",
    "agy-cli__gemini-3.8-flash-medium",
    "claude-cli__claude-haiku-5-5@medium",
    "codex-cli__gpt-6.1-terra@medium",
    "claude-cli__claude-fable-5-1@medium",
    "replay-cli__claude-fable-5-1@medium",
    "agy-cli__gpt-oss-120b-medium",
)
COND_PRIORITY = ("base", "base_mt")

# プロンプトに出すタスクの説明（skill_src/prompts の Goal 行から短くしたもの）と、そのタスクの API
TASK_INFO = {
    "stack": {
        "title": "cube stacking (single arm)",
        "goal": "Pick up the red cube and gently stack it on top of the green cube, then release it.",
        "prompt": "base_stack.txt",
    },
    "restack": {
        "title": "cube restacking (single arm)",
        "goal": "Gently place the red cube on top of the green cube and then open the gripper "
                "(at the start the cubes may already be stacked the other way round).",
        "prompt": "base_mt_restack.txt",
    },
    "nut": {
        "title": "nut assembly (single arm)",
        "goal": "Grasp the brown square nut by its handle and insert it onto the brown square block (peg).",
        "prompt": "base_nut.txt",
    },
    "handover": {
        "title": "two-arm hammer handover",
        "goal": "Arm 0 picks up the hammer, lifts it and hands it over to Arm 1, which grasps the handle; "
                "the hammer must stay at z between 0.15 and 0.20 during the handover.",
        "prompt": "base_handover.txt",
    },
}

HEADER = """Reference examples (skill library):
The programs below are complete solutions that SUCCEEDED on OTHER tasks of this benchmark (written by stronger models).
They are not solutions for the current task. Reuse their patterns where they fit, for example: computing heights from object extents,
keeping the grasp offset between the gripper and the object, rigid transforms with scipy, safe approach / lift / step-wise motions,
and checking the state with prints before finishing.
They were written for other objects and possibly other APIs: call ONLY the APIs listed for the current task below."""


def api_names(prompt_file: str) -> list[str]:
    """プロンプトの APIs 欄から関数名を取り出す。"""
    apis = prompt_text(prompt_file).split("APIs:", 1)[1]
    return re.findall(r"^([a-z_0-9]+)\(", apis, flags=re.M)


def prompt_text(prompt_file: str) -> str:
    """initial_prompt.txt（メッセージのリストの repr）から user の文面を取り出す。"""
    msgs = ast.literal_eval((SRC / "prompts" / prompt_file).read_text())
    return msgs[-1]["content"][0]["text"]


ALL_API = sorted({n for info in TASK_INFO.values() for n in api_names(info["prompt"])})


def split_blocks(code: str) -> list[str]:
    """「# Code block N」で区切られたコードをブロックに分ける（見出し行は除く）。"""
    parts = re.split(r"^# Code block \d+\s*$", code, flags=re.M)
    return [p.strip("\n") for p in parts if p.strip()]


def free_names(code: str) -> set[str]:
    """コードの中で定義されずに使われている名前（組み込み・API を除く）。スコープは大まかに見る。"""
    tree = ast.parse(code)
    defined: set[str] = set()
    used: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            (defined if isinstance(node.ctx, (ast.Store, ast.Del)) else used).add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                defined.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            defined.add(node.name)
    return used - defined - set(dir(builtins)) - set(ALL_API)


def example_code(path: Path) -> tuple[str, str]:
    """(見本にするコード, どの部分か) を返す。"""
    blocks = split_blocks(path.read_text())
    if len(blocks) == 1:
        return blocks[0], "all"
    last = blocks[-1]
    if not free_names(last):
        return last, f"last block ({len(blocks)} blocks)"
    return "\n\n".join(f"# --- turn {i + 1} ---\n{b}" for i, b in enumerate(blocks)), f"all {len(blocks)} blocks"


def pick(rows: list[dict], task: str, per_task: int) -> list[dict]:
    cands = [r for r in rows if r["task"] == task]
    for model in MODEL_PRIORITY:
        for cond in COND_PRIORITY:
            group = [r for r in cands if r["model"] == model and r["cond"] == cond]
            if not group:
                continue
            group.sort(key=lambda r: (int(r["bytes"]), int(r["trial"])))
            seen, chosen = set(), []
            for r in group:
                if r["sha1"] in seen:
                    continue
                seen.add(r["sha1"])
                chosen.append(r)
                if len(chosen) == per_task:
                    return chosen
            if chosen:
                return chosen
    raise RuntimeError(f"no successful code for {task}")


def est_tokens(text: str) -> int:
    """トークン数の目安（英語とコードで 1 トークン ≈ 3.2 文字。Qwen の語彙なら少なめに出る）。"""
    return round(len(text) / 3.2)


def render(target: str, picked: list[tuple[str, dict, str, str]]) -> str:
    parts = [HEADER]
    for i, (src_task, _row, code, _part) in enumerate(picked, 1):
        info = TASK_INFO[src_task]
        apis = ", ".join(api_names(info["prompt"]))
        parts.append(
            f"### Example {i}: {info['title']}\n"
            f"Goal of that task: {info['goal']}\n"
            f"APIs of that task: {apis}\n"
            f"```python\n{code.strip()}\n```"
        )
    parts.append("(End of reference examples. Now write the code for the current task described above.)")
    return "\n\n".join(parts) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-task", type=int, default=1, help="見本にするタスクごとの件数")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(SRC / "index.csv")))
    OUT.mkdir(exist_ok=True)
    sel_rows = []
    for target in TARGETS:
        picked = []
        for src_task in SOURCES[target]:
            assert src_task != target
            for r in pick(rows, src_task, args.per_task):
                code, part = example_code(SRC / r["file"])
                picked.append((src_task, r, code, part))
        text = render(target, picked)
        (OUT / f"{target}.md").write_text(text)
        base_prompt = prompt_text(TASK_INFO[target]["prompt"])
        print(f"{target}: {len(picked)} examples, {len(text)} chars (~{est_tokens(text)} tok); "
              f"base prompt ~{est_tokens(base_prompt)} tok -> total ~{est_tokens(text) + est_tokens(base_prompt)} tok")
        for src_task, r, code, part in picked:
            print(f"   {src_task:9s} {r['file']}  [{part}, {code.count(chr(10)) + 1} lines]")
            sel_rows.append({
                "target": target, "source_task": src_task, "file": r["file"], "model": r["model"],
                "cond": r["cond"], "trial": r["trial"], "part": part, "sha1": r["sha1"],
                "lines_used": code.count("\n") + 1,
            })
    with open(OUT / "selection.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sel_rows[0]))
        w.writeheader()
        w.writerows(sel_rows)
    print(f"wrote {OUT.relative_to(ROOT)}/{{{','.join(TARGETS)}}}.md and selection.csv")


if __name__ == "__main__":
    main()
