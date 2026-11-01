"""レポート用の表・検定・図を作り、下書き（report/report_draft.md）に数字を差し込む。

  python3 scripts/make_report.py

読むもの（正式な値。results/all_summary.md の注記と同じ出どころ）:
- Claude（Haiku・Opus）・Gemini・GPT-OSS: results/main_cells.csv
- Codex（terra・sol・astra）: results/clean_cells.csv（runs/main の Codex は点検の比較用）
- Fable: 1回で答える6セルは results/clean_cells.csv、複数ターン4セルは cloud_runs/cloud/summary.csv
- 正解コード: results/oracle_cells.csv
- 実験2（Qwen3.5-9B、Colab。作業中は「案A」と呼んでいたので、ファイル名は planA_*）: results/planA_cells.csv と results/planA_trials.csv（無ければ6章は空欄のまま）

書き出すもの:
- report/tables/*.csv と *.md（成功率と 95% 信頼区間、検定、平均化の集計）
- report/figs/*.png
- report/report_draft.md（report/report_template.md の {{キー}} を数字に置き換えたもの）

数字は全部 CSV から計算する。results/all_summary.md の表と食い違ったら止まる。
必要なのは matplotlib だけ（Wilson 区間と Fisher の正確検定はここで計算する）。
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
OUT = ROOT / "report"
FIGS = OUT / "figs"
TABLES = OUT / "tables"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_averaging import SOURCES as SCAN_SOURCES  # noqa: E402
from scan_averaging import kind as is_averaging  # noqa: E402

# ---------------------------------------------------------------- モデルとセル

# (表示名, 会社, 1回で答える条件の出どころ, 複数ターンの出どころ)
# 出どころ = (ファイルのタグ, CSV の model 列)
MODELS = [
    ("Claude Haiku 5.5", "Anthropic", ("main", "claude-cli/claude-haiku-5-5@medium"), None),
    ("Claude Opus 5.5", "Anthropic", ("main", "claude-cli/claude-opus-5-5@medium"), None),
    ("Claude Fable 5.1", "Anthropic", ("clean", "replay-cli/claude-fable-5-1@medium"),
     ("cloud", "claude-cli/claude-fable-5-1@medium")),
    ("gpt-6.1-terra", "OpenAI", ("clean", "codex-cli/gpt-6.1-terra@medium"), None),
    ("gpt-6.1-sol", "OpenAI", ("clean", "codex-cli/gpt-6.1-sol@medium"), None),
    ("gpt-6-astra", "OpenAI", ("clean", "codex-cli/gpt-6-astra@medium"), None),
    ("Gemini 3.8 Flash", "Google", ("main", "agy-cli/gemini-3.8-flash-medium"), None),
    ("Gemini 4 Argon", "Google", ("main", "agy-cli/gemini-4-argon-medium"), None),
    ("GPT-OSS 120B", "GPT-OSS（オープン）", ("main", "agy-cli/gpt-oss-120b-medium"), None),
]
# 下書きのキーに使う短い名前
SHORT = {
    "Claude Haiku 5.5": "haiku", "Claude Opus 5.5": "opus", "Claude Fable 5.1": "fable",
    "gpt-6.1-terra": "terra", "gpt-6.1-sol": "sol", "gpt-6-astra": "astra",
    "Gemini 3.8 Flash": "flash", "Gemini 4 Argon": "argon", "GPT-OSS 120B": "oss",
}
# runs/main にもある Codex（点検の比較用）
CODEX_MAIN = {"gpt-6.1-terra": "codex-cli/gpt-6.1-terra@medium", "gpt-6.1-sol": "codex-cli/gpt-6.1-sol@medium"}

CELLS = [
    ("base", "stack", "積む"),
    ("base", "nut", "ナット"),
    ("base", "restack", "積み替え"),
    ("base", "handover", "受け渡し"),
    ("base_mt", "restack", "積み替え(複数)"),
    ("base_mt", "handover", "受け渡し(複数)"),
    ("noisy", "stack", "誤差:積む"),
    ("noisy", "nut", "誤差:ナット"),
    ("noisy_mt", "stack", "誤差複数:積む"),
    ("noisy_mt", "nut", "誤差複数:ナット"),
]
TASK_JA = {"stack": "積む", "nut": "ナット", "restack": "積み替え", "handover": "受け渡し"}
COND_JA = {"base": "1回", "base_mt": "複数ターン", "noisy": "誤差あり・1回", "noisy_mt": "誤差あり・複数ターン"}

# 色（会社ごと。dataviz の既定パレットの先頭4色、隣どうしの色覚の差を検証済み）
VENDOR_COLOR = {"Anthropic": "#2a78d6", "OpenAI": "#eb6834", "Google": "#1baf7a", "GPT-OSS（オープン）": "#eda100"}
COND_COLOR = {"1回": "#2a78d6", "複数ターン": "#eb6834", "誤差あり・1回": "#1baf7a", "誤差あり・複数ターン": "#eda100"}
COND_HATCH = {"1回": "", "複数ターン": "//", "誤差あり・1回": "//", "誤差あり・複数ターン": ".."}


def wrap(label: str) -> str:
    """図の軸ラベル用に、モデル名を2行にする。"""
    return label.replace(" ", "\n", 1)


INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


# ---------------------------------------------------------------- 統計

def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson の 95% 信頼区間（割合）。"""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def fisher(k1: int, n1: int, k2: int, n2: int) -> float:
    """2×2 表 [[k1, n1-k1], [k2, n2-k2]] の Fisher の正確検定（両側）。"""
    K, N = k1 + k2, n1 + n2
    lo, hi = max(0, K - n2), min(K, n1)

    def pmf(x: int) -> float:
        return math.comb(n1, x) * math.comb(n2, K - x) / math.comb(N, K)

    p_obs = pmf(k1)
    return min(1.0, sum(pmf(x) for x in range(lo, hi + 1) if pmf(x) <= p_obs * (1 + 1e-7)))


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def fmt_p(p: float) -> str:
    if p < 0.0001:
        return "<0.0001"
    if p < 0.001:
        return f"{p:.4f}"
    return f"{p:.3f}"


def fmt_ci(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{round(100 * lo)}–{round(100 * hi)}%"


# ---------------------------------------------------------------- 読み込み

def read_cells() -> dict[tuple[str, str, str, str], tuple[int, int]]:
    """(タグ, 条件, model 列, タスク) → (成功, 試行)。"""
    out: dict[tuple[str, str, str, str], tuple[int, int]] = {}
    for tag, path in [("main", RES / "main_cells.csv"), ("clean", RES / "clean_cells.csv"),
                      ("oracle", RES / "oracle_cells.csv"), ("cloud", ROOT / "cloud_runs/cloud/summary.csv"),
                      ("casea", RES / "planA_cells.csv")]:
        if not path.exists():
            continue
        with path.open() as f:
            for r in csv.DictReader(f):
                out[(tag, r["cond"], r["model"], r["task"])] = (int(r["success"]), int(r["trials"]))
    return out


def official(raw, label: str, cond: str, task: str) -> tuple[int, int]:
    _, _, single, multi = next(m for m in MODELS if m[0] == label)
    tag, mid = multi if (multi and cond.endswith("_mt")) else single
    return raw[(tag, cond, mid, task)]


def check_all_summary(grid: dict[str, dict[tuple[str, str], tuple[int, int]]]) -> None:
    """results/all_summary.md の表と同じか確かめる（手で写した表との食い違いを防ぐ）。"""
    text = (RES / "all_summary.md").read_text()
    seen = 0
    for line in text.splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) != 12 or cols[0] not in grid:
            continue
        nums = [int(c.rstrip("*")) for c in cols[1:]]
        mine = [grid[cols[0]][(c, t)][0] for c, t, _ in CELLS]
        if nums[:10] != mine or nums[10] != sum(mine):
            sys.exit(f"all_summary.md と食い違い: {cols[0]} {nums} vs {mine}")
        seen += 1
    if seen != len(MODELS):
        sys.exit(f"all_summary.md の行が {seen} 個しか見つからない")


# ---------------------------------------------------------------- 書き出し

def write_table(name: str, header: list[str], rows: list[list], note: str = "") -> str:
    TABLES.mkdir(parents=True, exist_ok=True)
    with (TABLES / f"{name}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    md = "| " + " | ".join(header) + " |\n|" + "---|" * len(header) + "\n"
    md += "".join("| " + " | ".join(str(c) for c in r) + " |\n" for r in rows)
    if note:
        md += "\n" + note + "\n"
    (TABLES / f"{name}.md").write_text(md)
    return md


def setup_mpl():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    want = ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans CJK JP", "IPAexGothic", "IPAGothic",
            "Yu Gothic", "Meiryo", "DejaVu Sans"]
    have = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        "font.family": [w for w in want if w in have] or ["DejaVu Sans"],
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
        "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 9, "axes.titlesize": 10, "legend.frameon": False, "hatch.color": SURFACE,
        "hatch.linewidth": 1.2,
    })
    return plt


def bar_err(ax, x, k, n, width, color, hatch="", label=None):
    rates = [a / b for a, b in zip(k, n)]
    cis = [wilson(a, b) for a, b in zip(k, n)]
    lo = [max(0.0, r - c[0]) for r, c in zip(rates, cis)]
    hi = [max(0.0, c[1] - r) for r, c in zip(rates, cis)]
    ax.bar(x, rates, width, color=color, hatch=hatch, label=label, edgecolor=SURFACE, linewidth=1)
    ax.errorbar(x, rates, yerr=[lo, hi], fmt="none", ecolor=INK2, elinewidth=0.9, capsize=2)


def fig_tasks(plt, grid) -> None:
    import matplotlib.patches as mpatches

    labels = [m[0] for m in MODELS]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.2), sharey=True)
    for ax, task in zip(axes.flat, ["stack", "nut", "restack", "handover"]):
        k = [grid[l][("base", task)][0] for l in labels]
        n = [grid[l][("base", task)][1] for l in labels]
        x = list(range(len(labels)))
        for i, m in enumerate(MODELS):
            bar_err(ax, [i], [k[i]], [n[i]], 0.72, VENDOR_COLOR[m[1]])
            ax.text(i, -0.02, f"{k[i]}", ha="center", va="top", fontsize=8, color=INK)
        ax.set_title(f"{TASK_JA[task]}（1回で答える）", loc="left", color=INK)
        ax.set_xticks(x, [wrap(l) for l in labels], fontsize=7.5)
        ax.tick_params(axis="x", pad=12)
        ax.set_ylim(0, 1.05)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "25", "50", "75", "100%"])
    handles = [mpatches.Patch(color=c, label=v) for v, c in VENDOR_COLOR.items()]
    fig.legend(handles=handles, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.0))
    fig.text(0.01, 0.005, "棒の下の数字は成功数/10。誤差棒は Wilson の 95% 信頼区間。", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    fig.savefig(FIGS / "fig1_tasks.png", dpi=200)
    plt.close(fig)


def fig_conditions(plt, grid) -> None:
    labels = [m[0] for m in MODELS]
    panels = [
        ("積み替え: 1回 → 複数ターン", [("base", "restack", "1回"), ("base_mt", "restack", "複数ターン")]),
        ("受け渡し: 1回 → 複数ターン", [("base", "handover", "1回"), ("base_mt", "handover", "複数ターン")]),
        ("積む: 誤差なし → 誤差あり", [("base", "stack", "1回"), ("noisy", "stack", "誤差あり・1回"),
                               ("noisy_mt", "stack", "誤差あり・複数ターン")]),
        ("ナット: 誤差なし → 誤差あり", [("base", "nut", "1回"), ("noisy", "nut", "誤差あり・1回"),
                                ("noisy_mt", "nut", "誤差あり・複数ターン")]),
    ]
    fig, axes = plt.subplots(4, 1, figsize=(9.5, 11.5), sharey=True)
    for ax, (title, series) in zip(axes, panels):
        w = 0.8 / len(series)
        for j, (cond, task, name) in enumerate(series):
            xs = [i - 0.4 + w * (j + 0.5) for i in range(len(labels))]
            k = [grid[l][(cond, task)][0] for l in labels]
            n = [grid[l][(cond, task)][1] for l in labels]
            lab = "誤差なし・1回" if (name == "1回" and len(series) == 3) else name
            bar_err(ax, xs, k, n, w * 0.92, COND_COLOR[name], COND_HATCH[name], lab)
        ax.set_title(title, loc="left", color=INK)
        ax.set_xticks(range(len(labels)), [wrap(l) for l in labels], fontsize=8)
        ax.set_ylim(0, 1.05)
        ax.set_yticks([0, 0.5, 1.0], ["0", "50", "100%"])
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    fig.text(0.01, 0.003, "誤差棒は Wilson の 95% 信頼区間（各10回）。数字は report/tables/success.md。", fontsize=8, color=INK2)
    fig.tight_layout(rect=(0, 0.01, 1, 1))
    fig.savefig(FIGS / "fig2_conditions.png", dpi=200)
    plt.close(fig)


def fig_total(plt, grid) -> None:
    import matplotlib.patches as mpatches

    rows = sorted(((sum(grid[m[0]][(c, t)][0] for c, t, _ in CELLS), m) for m in MODELS), key=lambda r: r[0])
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for i, (tot, m) in enumerate(rows):
        ax.barh(i, tot, 0.66, color=VENDOR_COLOR[m[1]], edgecolor=SURFACE)
        ax.text(tot + 1, i, f"{tot}", va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(rows)), [m[0] for _, m in rows])
    ax.set_xlim(0, 100)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("合計の成功数（10セル × 10回 = 100）")
    handles = [mpatches.Patch(color=c, label=v) for v, c in VENDOR_COLOR.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGS / "fig3_total.png", dpi=200)
    plt.close(fig)


def fig_heatmap(plt, grid) -> None:
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("blue", ["#f4f8fd", "#cde2fb", "#86b6ef", "#2a78d6", "#184f95", "#0d366b"])
    labels = [m[0] for m in MODELS]
    data = [[grid[l][(c, t)][0] for c, t, _ in CELLS] for l in labels]
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.imshow(data, cmap=cmap, vmin=0, vmax=10, aspect="auto")
    for i, row in enumerate(data):
        for j, v in enumerate(row):
            ax.text(j, i, str(v), ha="center", va="center", fontsize=9, color=SURFACE if v >= 6 else INK)
    ax.set_xticks(range(len(CELLS)), [c[2] for c in CELLS], rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.axvline(5.5, color=SURFACE, linewidth=3)
    ax.axvline(3.5, color=SURFACE, linewidth=3)
    ax.set_title("成功数/10（左4列: 1回、中2列: 複数ターン、右4列: 位置に 1cm の誤差）", loc="left", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(FIGS / "fig0_heatmap.png", dpi=200)
    plt.close(fig)


CASEA_CONDS = [("base", "そのまま"), ("base_mt", "①複数ターン"), ("skill", "②見本"), ("skill_mt", "①＋②")]


def casea_errors() -> list[list]:
    """実験2 の1回で答える条件（base・skill）で、各試行のコードが最後にどの例外で止まったか（runs/planA の summary.txt）。
    試行のフォルダは results/planA_trials.csv の行（コードが落ちたか・成功したか）と名前が合うものを使う。
    複数ターンは1試行に複数のフォルダがあり、Colab から持ち帰ると更新時刻がそろって順番が分からないので数えない。
    runs/ が無い環境では、前に書き出した report/tables/casea_errors.csv を読み直す。"""
    cache = TABLES / "casea_errors.csv"
    base = ROOT / "runs/planA"
    if not base.exists():
        if not cache.exists():
            return []
        with cache.open() as f:
            return [r for i, r in enumerate(csv.reader(f)) if i > 0]
    rows = []
    with (RES / "planA_trials.csv").open() as f:
        trials = [r for r in csv.DictReader(f) if r["cond"] in ("base", "skill")]
    for r in trials:
        d = base / r["cond"] / "qwen3.5-9b/qwen3.5-9b" / r["task"]
        hits = sorted(d.glob(f"trial_{int(r['trial']):02d}_sandboxrc_{r['code_failed']}_reward_*"
                             f"_taskcompleted_{r['success']}"))
        if len(hits) != 1:
            sys.exit(f"実験2 の試行のフォルダが1つに決まらない: {d} trial {r['trial']} → {hits}")
        text = (hits[0] / "summary.txt").read_text(errors="replace")
        errs = re.findall(r"^(\w+(?:Error|Exception)): ?(.*)$", text, re.M)
        name, msg = errs[-1] if errs else ("", "")
        m = re.search(r"name '(\w+)' is not defined", msg)
        rows.append([r["cond"], r["task"], r["trial"], name, m.group(1) if m else "", r["success"]])
    return rows


def fig_casea(plt, raw) -> bool:
    rows = [(k, v) for k, v in raw.items() if k[0] == "casea"]
    if not rows:
        return False
    tasks = ["stack", "nut", "handover"]
    fig, ax = plt.subplots(figsize=(7, 3.6))
    w = 0.2
    colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    for j, (cond, lab) in enumerate(CASEA_CONDS):
        ks, ns, xs = [], [], []
        for i, t in enumerate(tasks):
            hit = [v for k, v in rows if k[1] == cond and k[3] == t]
            if hit:
                ks.append(hit[0][0]); ns.append(hit[0][1]); xs.append(i - 0.3 + w * j)
        if ks:
            bar_err(ax, xs, ks, ns, w * 0.92, colors[j], label=f"{cond}（{lab}）")
    ax.set_xticks(range(len(tasks)), [TASK_JA[t] for t in tasks])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("成功率（誤差棒は 95% 区間）")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=8)
    ax.set_title("実験2: Qwen3.5-9B の成功率（各10回）", loc="left")
    fig.tight_layout()
    fig.savefig(FIGS / "fig5_casea.png", dpi=200)
    plt.close(fig)
    return True


# ---------------------------------------------------------------- 平均化の集計

def trial_dirs_final(cell_dir: Path) -> list[tuple[Path, int]]:
    """試行ごとに最終のフォルダを選ぶ。動画があるものを最終とする（cloud_runs/ENV.md）。
    動画が無ければ更新時刻の新しいもの（scan_averaging.py と同じ）。"""
    pat = re.compile(r"trial_(\d+)_sandboxrc_(-?\d+)_reward_([-\d.]+)_taskcompleted_(\d)")
    best: dict[int, tuple[tuple[int, float], Path, int]] = {}
    for d in cell_dir.glob("trial_*"):
        m = pat.search(d.name)
        if not m:
            continue
        key = ((d / "video_combined.mp4").exists(), d.stat().st_mtime)
        t = int(m.group(1))
        if t not in best or key > best[t][0]:
            best[t] = (key, d, int(m.group(4)))
    return [(d, ok) for _, d, ok in best.values()]


def averaging_rows() -> tuple[list[list], bool]:
    """(モデル, 条件, タスク, 平均化した試行, 平均化ありの成功, 平均化なしの成功, 出どころ)。"""
    rows: list[list] = []
    label_of = {}
    for m in MODELS:
        for src in (m[2], m[3]):
            if src:
                label_of[src[1].replace("/", "__")] = m[0]
    have_runs = (ROOT / "runs").exists()
    cells: list[tuple[str, str, str, Path]] = []
    if have_runs:
        for tag, models in SCAN_SOURCES.items():
            for mid in models:
                for cond in ["noisy", "noisy_mt"]:
                    for task in ["stack", "nut"]:
                        for d in sorted((ROOT / "runs" / tag / cond / mid).glob(f"*/{task}")):
                            cells.append((label_of.get(mid, mid), cond, task, d))
    for cond in ["noisy_mt"]:
        for task in ["stack", "nut"]:
            d = ROOT / "cloud_runs/cloud" / cond / task
            if d.exists():
                cells.append(("Claude Fable 5.1", cond, task, d))
    for label, cond, task, d in cells:
        tr = trial_dirs_final(d)
        flags = [(is_averaging((p / "code.py").read_text()) if (p / "code.py").exists() else False, ok) for p, ok in tr]
        a = [ok for av, ok in flags if av]
        n = [ok for av, ok in flags if not av]
        src = str(d.relative_to(ROOT))
        rows.append([label, COND_JA[cond], TASK_JA[task], f"{len(a)}/{len(flags)}", f"{sum(a)}/{len(a)}",
                     f"{sum(n)}/{len(n)}", src])
    return rows, have_runs


def replay_averaging() -> list[list]:
    """Fable の1回で答える誤差ありの回答（replay/）に、平均化が何回あるか（成功との対応は取れない）。"""
    base = ROOT / "replay/claude-fable-5-1@medium"
    cells = json.loads((base / "cells.json").read_text())
    rows = []
    for h, name in cells.items():
        cond, task = name.split("/")
        if cond != "noisy":
            continue
        texts = [json.loads(p.read_text())["text"] for p in sorted((base / h / "responses").glob("*.json"))]
        codes = ["\n".join(re.findall(r"```python\n(.*?)```", t, re.S)) or t for t in texts]
        rows.append(["Claude Fable 5.1", COND_JA[cond], TASK_JA[task], f"{sum(map(is_averaging, codes))}/{len(codes)}",
                     "（対応なし）", "（対応なし）", str((base / h).relative_to(ROOT))])
    return rows


# README の「結果の要約」に入れる文（数字は {{キー}} で差し込む）
README_RESULTS = """成功数/10（9モデル×10セル、effort はすべて medium）

{{table.success_short}}
Claude Fable 5.1 の複数ターン4セル（積み替え(複数)・受け渡し(複数)・誤差複数）はクラウドの Linux、ほかは手元の Mac で回した。

合計の順位: {{total.rank}}。

![全セルの成功数](report/figs/fig0_heatmap.png)

- **積む**はほぼ全モデルが満点（9モデル合計 {{pool.base.stack}}）。差が出るのは**受け渡し**（両腕の協調）と**ナット**（向きを合わせる）。
- **受け渡し**は gpt-6.1-sol・gpt-6-astra が {{sol.base.handover}}・{{astra.base.handover}}、gpt-6.1-terra・Claude Fable 5.1・GPT-OSS 120B が {{terra.base.handover}}・{{fable.base.handover}}・{{oss.base.handover}}（Fisher の正確検定で p≤{{hand.base.maxp}}）。
- **積み替え**（最初から緑が赤の上に載っている）は、1回で答えると全モデル 0/10。複数ターンにすると Gemini 4 Argon だけが {{argon.base_mt.restack}} になり（p={{p.mt.argon.restack}}、多重比較の補正後は言い切れない）、成功はすべて実行結果を見て書き直した試行だった。書き直さずに「完了」と答えるモデルには、複数ターンが効かない。
- **位置に 1cm の誤差**を足すと、9モデル合計でナットが {{pool.base.nut}}→{{pool.noisy.nut}}（p={{p.noise.pool.nut}}）に下がった。大きく下がったのは Gemini 3.8 Flash（{{flash.base.nut}}→{{flash.noisy.nut}}）と Claude Haiku 5.5（{{haiku.base.nut}}→{{haiku.noisy.nut}}）。ただし誤差ありのセルは、回し直すと1セルで最大 {{codex.maxdiff}} 回ぶれるので、10回での細かい差は言い切れない。
- **実験2: 小型オープンモデルの底上げ**（Qwen3.5-9B、Colab の A100）: そのままでは積む・ナット・受け渡しが {{qa.base.stack}}・{{qa.base.nut}}・{{qa.base.handover}}。①実行結果を見て書き直す、②大きいモデルの成功コード（ほかのタスクの分）を見本に足す、を入れると積むは {{qa.base_mt.stack}}・{{qa.skill.stack}}・{{qa.skill_mt.stack}}（①・②・①＋②）に上がった。1つずつでは 10回では言い切れない（p≥{{p.qa.stack.skill_mt}}）が、3条件まとめると {{qa.stack.pooled}} 対 {{qa.base.stack}}（p={{p.qa.stack.pooled}}）で、何かを足すと上がることはほぼ言える。①と②のどちらが効いたかは区別できない。ナットと受け渡しはほぼ 0 のまま。①で成功した試行も、{{qa.base_mt.succ_first}} は書き直さずに最初のコードで成功していた。

"""


# ---------------------------------------------------------------- 本体

def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    raw = read_cells()
    grid = {m[0]: {(c, t): official(raw, m[0], c, t) for c, t, _ in CELLS} for m in MODELS}
    check_all_summary(grid)
    V: dict[str, str] = {}  # 下書きに差し込む値

    # --- 表1: 成功数と信頼区間
    rows = []
    for m in MODELS:
        r = [m[0]]
        for c, t, _ in CELLS:
            k, n = grid[m[0]][(c, t)]
            r.append(f"{k}/{n} ({fmt_ci(k, n)})")
            V[f"{SHORT[m[0]]}.{c}.{t}"] = f"{k}/{n}"
            V[f"{SHORT[m[0]]}.{c}.{t}.k"] = str(k)
        tot = sum(grid[m[0]][(c, t)][0] for c, t, _ in CELLS)
        V[f"{SHORT[m[0]]}.total"] = str(tot)
        r.append(tot)
        rows.append(r)
    V["table.success"] = write_table(
        "success", ["モデル"] + [c[2] for c in CELLS] + ["合計/100"], rows,
        "成功数/10（括弧は Wilson の 95% 信頼区間）。Fable の複数ターン（積み替え(複数)・受け渡し(複数)・誤差複数）は"
        "クラウドの Linux、ほかは手元の Mac。")
    # 短い表（数字だけ、本文用）
    rows_s = [[m[0]] + [grid[m[0]][(c, t)][0] for c, t, _ in CELLS] + [sum(grid[m[0]][(c, t)][0] for c, t, _ in CELLS)]
              for m in MODELS]
    V["table.success_short"] = write_table("success_short", ["モデル"] + [c[2] for c in CELLS] + ["合計/100"], rows_s)

    # 合計の順位
    rank = sorted(MODELS, key=lambda m: -int(V[f"{SHORT[m[0]]}.total"]))
    V["total.rank"] = "、".join(f"{m[0]}（{V[SHORT[m[0]] + '.total']}）" for m in rank)
    rows_t = []
    for i, m in enumerate(rank, 1):
        tot = int(V[f"{SHORT[m[0]]}.total"])
        rows_t.append([i, m[0], m[1], tot, fmt_ci(tot, 100)])
    V["table.total"] = write_table("total", ["順位", "モデル", "会社", "合計/100", "95% 区間（参考）"], rows_t,
                                   "95% 区間は100試行を独立とみなした目安。セルごとに難しさが違うので、厳密な区間ではない。")

    # --- 検定
    tests: list[dict] = []

    def add(group: str, key: str, name: str, a: tuple[int, int], b: tuple[int, int]) -> None:
        p = fisher(a[0], a[1], b[0], b[1])
        tests.append({"group": group, "key": key, "name": name, "a": a, "b": b, "p": p})
        V[f"p.{key}"] = fmt_p(p)

    g = lambda l, c, t: grid[l][(c, t)]  # noqa: E731
    # (1) 受け渡し: sol・astra と terra・Fable・GPT-OSS
    for c in ["base", "base_mt"]:
        for hi in ["gpt-6.1-sol", "gpt-6-astra"]:
            for lo in ["gpt-6.1-terra", "Claude Fable 5.1", "GPT-OSS 120B"]:
                add("受け渡し", f"hand.{c}.{SHORT[hi]}.{SHORT[lo]}", f"{COND_JA[c]}の受け渡し: {hi} vs {lo}",
                    g(hi, c, "handover"), g(lo, c, "handover"))
    # (2) 誤差の有無（1回）: 誤差なし vs 誤差あり
    for m in MODELS:
        for t in ["nut", "stack"]:
            add("誤差", f"noise.{SHORT[m[0]]}.{t}", f"{m[0]} の{TASK_JA[t]}: 誤差なし vs 誤差あり（1回）",
                g(m[0], "base", t), g(m[0], "noisy", t))
    pool = lambda c, t: (sum(g(m[0], c, t)[0] for m in MODELS), sum(g(m[0], c, t)[1] for m in MODELS))  # noqa: E731
    for t in ["nut", "stack"]:
        a, b = pool("base", t), pool("noisy", t)
        add("誤差（全モデル合算）", f"noise.pool.{t}", f"9モデル合算の{TASK_JA[t]}: 誤差なし vs 誤差あり", a, b)
        V[f"pool.base.{t}"] = f"{a[0]}/{a[1]}"
        V[f"pool.noisy.{t}"] = f"{b[0]}/{b[1]}"
        c2 = pool("noisy_mt", t)
        V[f"pool.noisy_mt.{t}"] = f"{c2[0]}/{c2[1]}"
        add("誤差（全モデル合算）", f"noisemt.pool.{t}", f"9モデル合算の{TASK_JA[t]}: 誤差あり 1回 vs 複数ターン", b, c2)
    # (3) 1回 vs 複数ターン
    for m in MODELS:
        for t in ["restack", "handover"]:
            add("複数ターン", f"mt.{SHORT[m[0]]}.{t}", f"{m[0]} の{TASK_JA[t]}: 1回 vs 複数ターン",
                g(m[0], "base", t), g(m[0], "base_mt", t))
        for t in ["stack", "nut"]:
            add("複数ターン（誤差あり）", f"nmt.{SHORT[m[0]]}.{t}", f"{m[0]} の誤差あり{TASK_JA[t]}: 1回 vs 複数ターン",
                g(m[0], "noisy", t), g(m[0], "noisy_mt", t))
    # (4) Codex: runs/main vs runs/clean（点検）
    diffs = []
    for label, mid in CODEX_MAIN.items():
        for c, t, cname in CELLS:
            a, b = raw[("main", c, mid, t)], raw[("clean", c, mid, t)]
            add("Codex 点検", f"codex.{SHORT[label]}.{c}.{t}", f"{label} の{cname}: main vs clean", a, b)
            diffs.append((abs(a[0] - b[0]), label, cname, a, b, c.startswith("noisy")))
    mx = max(diffs, key=lambda d: (d[0], d[5]))
    V["codex.maxdiff"] = str(mx[0])
    V["codex.maxdiff.where"] = f"{mx[1]} の{mx[2]}（{mx[3][0]}→{mx[4][0]}）"
    V["codex.maxdiff.base"] = str(max(d[0] for d in diffs if not d[5]))
    codex_ps = [t["p"] for t in tests if t["group"] == "Codex 点検"]
    V["codex.minp"] = fmt_p(min(codex_ps))
    for label, mid in CODEX_MAIN.items():
        a = sum(raw[("main", c, mid, t)][0] for c, t, _ in CELLS)
        b = sum(raw[("clean", c, mid, t)][0] for c, t, _ in CELLS)
        V[f"codex.{SHORT[label]}.total_main"] = str(a)
        V[f"codex.{SHORT[label]}.total_clean"] = str(b)
    # (5) 正解コード: 誤差あり vs 平均化
    orows = []
    for t in ["stack", "restack", "nut", "wipe"]:
        a, b = raw[("oracle", "noisy", "oracle", t)], raw[("oracle", "check_avg", "oracle", t)]
        add("正解コード", f"oracle.{t}", f"正解コードの{TASK_JA.get(t, '拭く')}: 誤差あり vs 平均化", a, b)
        orows.append([TASK_JA.get(t, "拭く"), f"{a[0]}/{a[1]}", f"{b[0]}/{b[1]}", V[f"p.oracle.{t}"]])
        V[f"oracle.noisy.{t}"] = f"{a[0]}/{a[1]}"
        V[f"oracle.avg.{t}"] = f"{b[0]}/{b[1]}"
    V["table.oracle"] = write_table("oracle_averaging", ["タスク", "誤差あり（そのまま）", "誤差あり（30回読んで平均）", "Fisher p"],
                                    orows, "正解コード（特権情報あり）を各5回。results/oracle_cells.csv の noisy と check_avg。")

    # Holm（主な比較のまとまりごと）
    for grp in sorted({t["group"] for t in tests}):
        sub = [t for t in tests if t["group"] == grp]
        for t, adj in zip(sub, holm([t["p"] for t in sub])):
            t["holm"] = adj
            V[f"holm.{t['key']}"] = fmt_p(adj)
    rows_f = [[t["group"], t["name"], f"{t['a'][0]}/{t['a'][1]}", f"{t['b'][0]}/{t['b'][1]}", fmt_p(t["p"]),
               fmt_p(t["holm"]), "○" if t["p"] < 0.05 else ""] for t in tests]
    write_table("fisher_all", ["まとまり", "比べたもの", "A", "B", "p（両側）", "p（Holm 補正）", "p<0.05"], rows_f,
                "Fisher の正確検定（両側）。Holm 補正は「まとまり」の中で行った。")

    hb = [t for t in tests if t["key"].startswith("hand.base.")]
    V["hand.base.maxp"] = fmt_p(max(t["p"] for t in hb))
    V["hand.base.maxholm"] = fmt_p(max(t["holm"] for t in hb))

    # 本文に載せる主な検定
    main_keys = [
        "hand.base.sol.terra", "hand.base.sol.fable", "hand.base.sol.oss", "hand.base.astra.terra",
        "hand.base.astra.fable", "hand.base.astra.oss",
        "noise.flash.nut", "noise.haiku.nut", "noise.oss.nut", "noise.pool.nut", "noise.pool.stack",
        "mt.argon.restack", "mt.flash.handover", "noisemt.pool.nut", "noisemt.pool.stack",
        "codex.terra.noisy_mt.nut", "codex.sol.noisy.nut", "codex.terra.base.handover",
        "oracle.stack", "oracle.restack", "oracle.nut",
    ]
    by_key = {t["key"]: t for t in tests}
    rows_m = [[by_key[k]["name"], f"{by_key[k]['a'][0]}/{by_key[k]['a'][1]}", f"{by_key[k]['b'][0]}/{by_key[k]['b'][1]}",
               fmt_p(by_key[k]["p"]), fmt_p(by_key[k]["holm"])] for k in main_keys]
    V["table.fisher_main"] = write_table("fisher_main", ["比べたもの", "A", "B", "p（両側）", "p（Holm 補正）"], rows_m,
                                         "全部の検定は report/tables/fisher_all.md。Holm 補正は同じまとまり"
                                         "（受け渡し12件・誤差18件・複数ターン18件など）の中で行った。")

    # 誤差の有無で p<0.05 になったモデル
    sig = [m[0] for m in MODELS if by_key[f"noise.{SHORT[m[0]]}.nut"]["p"] < 0.05]
    V["noise.nut.sig"] = "、".join(sig) if sig else "なし"
    V["noise.nut.sig.n"] = str(len(sig))
    V["noise.nut.sig.holm"] = "、".join(m[0] for m in MODELS if by_key[f"noise.{SHORT[m[0]]}.nut"]["holm"] < 0.05) or "なし"
    sigmt = [t["name"] for t in tests if t["group"] == "複数ターン" and t["p"] < 0.05]
    V["mt.sig"] = "、".join(sigmt) if sigmt else "なし"
    signmt = [t["name"] for t in tests if t["group"] == "複数ターン（誤差あり）" and t["p"] < 0.05]
    V["nmt.sig"] = "、".join(signmt) if signmt else "なし"
    V["codex.n_sig"] = str(sum(p < 0.05 for p in codex_ps))
    V["codex.n"] = str(len(codex_ps))

    # --- 10回ずつで p<0.05 に必要な差
    rows_d = []
    for k1 in range(0, 11):
        need = None
        for d in range(1, 11):
            ok = [k2 for k2 in (k1 - d, k1 + d) if 0 <= k2 <= 10 and fisher(k1, 10, k2, 10) < 0.05]
            if ok:
                need = (d, ok)
                break
        rows_d.append([f"{k1}/10", need[0] if need else "（なし）",
                       "、".join(f"{x}/10" for x in need[1]) if need else ""])
    V["table.mindiff"] = write_table("min_difference", ["片方", "p<0.05 に必要な差（回）", "その相手"], rows_d,
                                     "10回 対 10回の Fisher の正確検定（両側）。")
    V["p.ex94"] = fmt_p(fisher(9, 10, 4, 10))
    V["mindiff.5"] = str(rows_d[5][1])
    V["mindiff.10"] = str(rows_d[10][1])
    V["mindiff.0"] = str(rows_d[0][1])

    # --- 複数ターンで書き直した試行（trials.csv の code_blocks）
    def trials(tag: str) -> list[dict]:
        p = RES / f"{tag}_trials.csv"
        return list(csv.DictReader(p.open())) if p.exists() else []

    tr = {"main": trials("main"), "clean": trials("clean")}

    def regen(label: str, cond: str, task: str) -> tuple[int, int, int]:
        """(成功のうち書き直した試行, 成功数, 書き直した試行)。"""
        tag, mid = next(m for m in MODELS if m[0] == label)[2]
        rs = [r for r in tr[tag] if r["cond"] == cond and r["model"] == mid and r["task"] == task]
        succ = [r for r in rs if r["success"] == "1"]
        return (sum(int(r["code_blocks"]) > 1 for r in succ), len(succ), sum(int(r["code_blocks"]) > 1 for r in rs))

    rr = []
    for m in MODELS:
        if m[3]:
            continue  # Fable の複数ターンは cloud（trials.csv が無い）
        for t in ["restack", "handover"]:
            a, b, c = regen(m[0], "base_mt", t)
            rr.append([m[0], TASK_JA[t], f"{c}/10", f"{a}/{b}"])
            V[f"regen.{SHORT[m[0]]}.{t}"] = f"{c}/10"
            V[f"regen.{SHORT[m[0]]}.{t}.succ"] = f"{a}/{b}"
    V["table.regen"] = write_table("multiturn_regen", ["モデル", "タスク", "書き直した試行", "成功のうち書き直した試行"], rr,
                                   "複数ターン（誤差なし）。コードブロックが2個以上の試行を「書き直した」とした"
                                   "（results/*_trials.csv の code_blocks）。Fable はクラウドの実行で trials.csv が無いので除いた。")

    # --- 呼び出し
    calls = list(csv.DictReader((RES / "main_calls.csv").open()))
    V["calls.main.n"] = f"{sum(int(r['calls']) for r in calls):,}"
    V["calls.main.err"] = str(sum(int(r["errors"]) for r in calls))
    official_src = {m[2] for m in MODELS}
    cf = []
    for tag in ["main", "clean"]:
        for r in csv.DictReader((RES / f"{tag}_cells.csv").open()):
            if (tag, r["model"]) in official_src and int(r["code_failed"]) > 0:
                label = next(m[0] for m in MODELS if m[2] == (tag, r["model"]))
                cf.append((label, r["cond"], r["task"], int(r["code_failed"])))
    V["code_failed.total"] = str(sum(c[3] for c in cf))
    V["code_failed.list"] = "、".join(f"{l} の{COND_JA[c]}・{TASK_JA[t]} {n}回" for l, c, t, n in cf) or "なし"

    # --- 平均化
    av_rows, have_runs = averaging_rows()
    if not have_runs:  # runs/ があれば Fable の1回の分は runs/clean で数えている（replay は同じ回答で、成功との対応が無い）
        av_rows += replay_averaging()
    note = ("scripts/scan_averaging.py と同じ判定（np.mean/median/average と range(...) があり、位置を読む関数を呼ぶ）。"
            "正規表現による目安で、取りこぼしがありうる。")
    if not have_runs:
        note += (" このリポジトリには runs/ が無いので、Fable（cloud_runs/ と replay/）だけを数えた。"
                 "ほかの8モデルは runs/ のある手元で `python3 scripts/make_report.py` を流し直すと埋まる。")
    V["table.averaging"] = write_table("averaging", ["モデル", "条件", "タスク", "平均化した試行", "成功（平均化あり）",
                                                     "成功（平均化なし）", "出どころ"], av_rows, note)
    for r in av_rows:
        if r[0] == "Claude Fable 5.1" and r[1] == COND_JA["noisy_mt"] and r[2] == TASK_JA["nut"]:
            V["avg.fable.noisy_mt.nut"] = r[3]
            V["avg.fable.noisy_mt.nut.succ"] = r[4]
    V["skill_src.n"] = str(sum(1 for _ in csv.DictReader((ROOT / "skill_src/index.csv").open())))
    V["averaging.have_runs"] = "あり" if have_runs else "なし"

    # --- 実験2（案A）
    plt = setup_mpl()
    has_a = fig_casea(plt, raw)
    if has_a:
        tasks_a = ["stack", "nut", "handover"]
        A = {(k[1], k[3]): v for k, v in raw.items() if k[0] == "casea"}
        with (RES / "planA_cells.csv").open() as f:
            failed = {(r["cond"], r["task"]): int(r["code_failed"]) for r in csv.DictReader(f)}
        with (RES / "planA_trials.csv").open() as f:
            trials_a = list(csv.DictReader(f))
        rows = []
        for c, lab in CASEA_CONDS:
            rows.append([f"{c}（{lab}）"] + [f"{A[(c, t)][0]}/{A[(c, t)][1]}（{failed[(c, t)]}）" for t in tasks_a]
                        + [f"{sum(A[(c, t)][0] for t in tasks_a)}/{sum(A[(c, t)][1] for t in tasks_a)}"])
            for t in tasks_a:
                V[f"qa.{c}.{t}"] = f"{A[(c, t)][0]}/{A[(c, t)][1]}"
            V[f"qa.{c}.failed"] = f"{sum(failed[(c, t)] for t in tasks_a)}/{sum(A[(c, t)][1] for t in tasks_a)}"
        # 参考: 大きいモデル9個の同じ3タスク（1回で答える条件）
        big = {t: sorted(grid[m[0]][("base", t)][0] for m in MODELS) for t in tasks_a}
        rows.append(["参考: 大きいモデル9個（そのまま）の中央値［最小–最大］"]
                    + [f"{big[t][len(big[t]) // 2]}/10［{big[t][0]}–{big[t][-1]}］" for t in tasks_a] + [""])
        V["table.casea"] = write_table(
            "casea", ["条件", "積む", "ナット", "受け渡し", "3タスクの合計"], rows,
            "括弧内は、コードが例外で止まった試行の数（複数ターンは最後のコード）。各セル10回。")
        for t in tasks_a:
            V[f"qa.big.{t}.median"] = f"{big[t][len(big[t]) // 2]}/10"
        # 積むの検定（そのまま と ①・②・①＋②）。10回ずつなので、差が5回ほど無いと言い切れない
        k0, n0 = A[("base", "stack")]
        for c, _ in CASEA_CONDS[1:]:
            V[f"p.qa.stack.{c}"] = fmt_p(fisher(*A[(c, "stack")], k0, n0))
        # 3条件（①・②・①＋②）をまとめて、そのままと比べる（結果を見てから決めた比べ方なので、本文でそう断る）
        kp = sum(A[(c, "stack")][0] for c, _ in CASEA_CONDS[1:])
        np_ = sum(A[(c, "stack")][1] for c, _ in CASEA_CONDS[1:])
        V["qa.stack.pooled"] = f"{kp}/{np_}"
        V["p.qa.stack.pooled"] = fmt_p(fisher(kp, np_, k0, n0))
        # 複数ターンで成功した試行のうち、書き直さずに最初のコードで成功したもの（regenerations=0）。
        # 書き直した試行が、書き直して初めて成功したのかは記録に残っていない（ターンごとの成否が無い）
        for c in ["base_mt", "skill_mt"]:
            ok = [r for r in trials_a if r["cond"] == c and r["success"] == "1"]
            if any(r["regenerations"] == "" for r in ok):
                sys.exit(f"planA_trials.csv の {c} に、書き直しの回数が空の成功試行がある（analyze.py を流し直す）")
            first = [r for r in ok if r["regenerations"] == "0"]
            V[f"qa.{c}.succ_first"] = f"{len(first)}/{len(ok)}"
            for t in tasks_a:
                ts = [r for r in trials_a if r["cond"] == c and r["task"] == t and r["code_blocks"] != ""]
                V[f"qa.{c}.{t}.blocks"] = f"{sum(int(r['code_blocks']) for r in ts) / len(ts):.1f}"
        # 例外の内訳（1回で答える条件）
        er = casea_errors()
        if er:
            write_table("casea_errors", ["cond", "task", "trial", "exception", "undefined_name", "success"], er)
            home = [r for r in er if r[0] == "skill" and r[1] == "stack" and r[4] == "goto_home_joint_position"]
            V["qa.skill.stack.home"] = str(len(home))
            V["qa.skill.stack.home.succ"] = str(sum(int(r[5]) for r in home))
            V["qa.syntax"] = str(sum(1 for r in er if r[3] in ("SyntaxError", "IndentationError")))
        else:
            for k in ["qa.skill.stack.home", "qa.skill.stack.home.succ", "qa.syntax"]:
                V[k] = "（runs/ が無いので未集計）"
        with (RES / "planA_calls.csv").open() as f:
            calls = next(csv.DictReader(f))
        V["qa.calls"] = calls["calls"]
        V["qa.calls.err"] = calls["errors"]
        V["qa.calls.latency"] = calls["median_latency_s"]
        V["fig.casea"] = "![実験2 の結果](figs/fig5_casea.png)"
    else:
        V["table.casea"] = ("| 条件 | 積む | ナット | 受け渡し |\n|---|---|---|---|\n"
                            "| base（そのまま・1回） | （未） | （未） | （未） |\n| base_mt（①あり・複数ターン） | （未） | （未） | （未） |\n"
                            "| skill（②あり・1回） | （未） | （未） | （未） |\n| skill_mt（①②あり・複数ターン） | （未） | （未） | （未） |\n\n"
                            "<!-- results/casea_cells.csv（cond,model,task,trials,success）を置いて make_report.py を流すと、"
                            "ここに表、下に図（figs/fig5_casea.png）が入る -->\n")
        V["fig.casea"] = "<!-- 図: figs/fig5_casea.png（実験2 の結果が入ると作られる） -->"

    # --- 図
    fig_heatmap(plt, grid)
    fig_tasks(plt, grid)
    fig_conditions(plt, grid)
    fig_total(plt, grid)

    (TABLES / "values.json").write_text(json.dumps(V, ensure_ascii=False, indent=1))

    # --- 下書き
    tpl = (OUT / "report_template.md").read_text()
    missing = sorted({k for k in re.findall(r"\{\{([^}]+)\}\}", tpl) if k not in V})
    if missing:
        sys.exit(f"下書きのキーが見つからない: {missing}")
    draft = re.sub(r"\{\{([^}]+)\}\}", lambda m: V[m.group(1)], tpl).replace("p=<", "p<")
    head = ("<!-- このファイルは scripts/make_report.py が report/report_template.md から作る。"
            "直すときはテンプレートの方を直す。 -->\n")
    (OUT / "report_draft.md").write_text(head + draft)
    # --- README の結果欄
    readme = ROOT / "README.md"
    if readme.exists():
        block = README_RESULTS
        for k in re.findall(r"\{\{([^}]+)\}\}", block):
            if k not in V:
                sys.exit(f"README のキーが見つからない: {k}")
        block = re.sub(r"\{\{([^}]+)\}\}", lambda m: V[m.group(1)], block).replace("p=<", "p<")
        text = readme.read_text()
        a = text.index("<!-- results:start")
        a = text.index("-->", a) + 3
        b = text.index("<!-- results:end -->")
        readme.write_text(text[:a] + "\n" + block + text[b:])
    print(f"wrote {OUT / 'report_draft.md'}, {len(list(FIGS.glob('*.png')))} figs, {len(list(TABLES.glob('*.md')))} tables")


if __name__ == "__main__":
    main()
