"""モデル × タスク × 条件の組み合わせで CaP-X を順に回し、成功数を集計する。

例:
  python scripts/run_grid.py --tag pilot --models claude-cli/claude-haiku-5-5 agy-cli/gemini-3.8-flash-low \
      --tasks stack nut --conds base --trials 3 --workers 3

結果は runs/<tag>/<cond>/<model>/<task>/ に CaP-X の出力がそのまま入り、
runs/<tag>/summary.csv に1行ずつ追記される。終わっている組み合わせは飛ばす。
事前に proxy/cli_proxy.py（ポート 8120）と PyRoKi サーバー（8116）を起動しておく。
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
# Linux（クラウド）では環境変数で変える。既定は Mac の置き場所。
CAPX = Path(os.getenv("CAPX_DIR", str(ROOT.parent / "third_party" / "cap-x")))
PY = Path(os.getenv("CAPX_PYTHON", str(CAPX / ".venv-mac" / "bin" / "python")))

# 特権情報ありの CaP-X 公式設定
TASKS = {
    "lift": "env_configs/cube_lifting/franka_robosuite_cube_lifting_privileged.yaml",
    "stack": "env_configs/cube_stack/franka_robosuite_cube_stack_privileged.yaml",
    "restack": "env_configs/cube_restack/franka_robosuite_cube_restack_privileged.yaml",
    "nut": "env_configs/nut_assembly/franka_robosuite_nut_assembly_privileged.yaml",
    "wipe": "env_configs/spill_wipe/franka_robosuite_spill_wipe_privileged.yaml",
    "handover": "env_configs/two_arm_handover/two_arm_handover_privileged.yaml",
}
# 条件ごとの設定ファイル置き場（base は公式そのまま）
COND_DIRS = {"base": None}


def config_for(task: str, cond: str) -> Path:
    if cond == "base":
        return CAPX / TASKS[task]
    path = ROOT / "configs" / cond / f"{task}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def count_results(out_dir: Path) -> tuple[int, int]:
    """CaP-X の最後の集計（launch.log）から、成功数と試行数を読む。

    CaP-X は試行のフォルダを <out_dir の親>/<モデル名>/<タスク> に書くので、
    フォルダを数えるより集計行を読む方が確実。
    """
    log = (out_dir / "launch.log").read_text(errors="replace") if (out_dir / "launch.log").exists() else ""
    total = re.findall(r"Total number of trials: (\d+)", log)
    stats = re.findall(r"Task completed:\s*\n\s*[\d.]+/[\d.]+/(\d+)", log)
    if not total or not stats:
        return 0, 0
    return int(stats[-1]), int(total[-1])


IK_URL = "http://127.0.0.1:8116/ik"
# 机の上あたりで手先を下向きにした、届く姿勢（wxyz + xyz）
IK_PROBE = {"target_pose_wxyz_xyz": [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]}


def ik_ok(timeout: float = 30.0) -> bool:
    try:
        r = requests.post(IK_URL, json=IK_PROBE, timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False


def restart_ik_server() -> None:
    """PyRoKi の IK サーバーを止めて起動し直す（macOS では並行処理で固まることがある）。"""
    pids = subprocess.run(["lsof", "-t", "-i", ":8116", "-sTCP:LISTEN"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        subprocess.run(["kill", "-9", pid])
    log = (ROOT / "logs" / "pyroki_server.log").open("a")
    subprocess.Popen(
        [str(PY), "-m", "capx.serving.launch_pyroki_server", "--port", "8116", "--host", "127.0.0.1"],
        cwd=CAPX, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    for _ in range(60):
        time.sleep(2)
        if ik_ok(timeout=10):
            return
    raise RuntimeError("IK server did not come back")


def ensure_ik_server() -> None:
    if not ik_ok():
        print("  IK server not responding; restarting", flush=True)
        restart_ik_server()


def ik_failed(out_dir: Path) -> bool:
    log = out_dir / "launch.log"
    return log.exists() and "8116/ik failed" in log.read_text(errors="replace")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--tasks", nargs="+", default=list(TASKS))
    ap.add_argument("--conds", nargs="+", default=["base"])
    ap.add_argument("--trials", type=int, default=10)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--video", action="store_true")
    args = ap.parse_args()

    run_root = ROOT / "runs" / args.tag
    run_root.mkdir(parents=True, exist_ok=True)
    summary = run_root / "summary.csv"
    new_file = not summary.exists()
    env = dict(os.environ, MUJOCO_GL=os.getenv("MUJOCO_GL", "cgl"), CAPX_LLM_TIMEOUT="600", CAPX_IK_TIMEOUT="60")

    with summary.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["cond", "model", "task", "success", "trials", "elapsed_s"])
        for cond in args.conds:
            for model in args.models:
                for task in args.tasks:
                    out_dir = run_root / cond / model.replace("/", "__") / task
                    if (out_dir / "DONE").exists():
                        print(f"skip {cond} {model} {task}")
                        continue
                    out_dir.mkdir(parents=True, exist_ok=True)
                    cmd = [
                        str(PY), "capx/envs/launch.py",
                        "--config-path", str(config_for(task, cond)),
                        "--model", model,
                        "--server-url", "http://127.0.0.1:8120/chat/completions",
                        "--total-trials", str(args.trials),
                        "--num-workers", str(args.workers),
                        "--record-video", str(args.video),
                        "--output-dir", str(out_dir),
                    ]
                    if model == "oracle":  # 人が書いた正解コードを流す
                        i = cmd.index("--model")
                        cmd[i : i + 2] = ["--use-oracle-code", "True"]
                    # CaP-X は試行のフォルダを <out_dir の親>/<モデル名>/<タスク> に書く
                    capx_out = out_dir.parent / model.replace("/", "_") / task
                    for attempt in range(1, 4):
                        ensure_ik_server()
                        shutil.rmtree(capx_out, ignore_errors=True)
                        start = time.time()
                        with (out_dir / "launch.log").open("w") as log:
                            subprocess.run(cmd, cwd=CAPX, env=env, stdout=log, stderr=subprocess.STDOUT)
                        elapsed = round(time.time() - start)
                        if not ik_failed(out_dir):
                            break
                        # IK サーバーが固まった回は結果に混ぜない。立て直してやり直す
                        print(f"  IK failure in {cond}/{model}/{task} (attempt {attempt}); restarting IK server", flush=True)
                        restart_ik_server()
                    ok, n = count_results(out_dir)
                    if ik_failed(out_dir):
                        print(f"  giving up on {cond}/{model}/{task}: IK kept failing", flush=True)
                        continue
                    writer.writerow([cond, model, task, ok, n, elapsed])
                    f.flush()
                    (out_dir / "DONE").write_text(f"{ok}/{n}\n")
                    print(f"{cond:8s} {model:40s} {task:9s} {ok}/{n}  ({elapsed}s)", flush=True)


if __name__ == "__main__":
    main()
