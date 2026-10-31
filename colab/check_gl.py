"""MuJoCo のオフスクリーン描画を egl → osmesa の順に試し、使える方を選ぶ。

各方式を別プロセスで起動し（MUJOCO_GL は import 前に決める必要があるため）、
640x480 を数十枚描いて速さ（枚/秒）と描画の実装名（GL_RENDERER: NVIDIA なら GPU、llvmpipe ならソフトウェア）を
記録する。最初に動いた方式を選ぶ。結果は JSON で --out に書き、選んだ方式を最後の行に出す。

  <CaP-X の python> colab/check_gl.py --out logs/gl_check.json [--order egl osmesa]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROBE = r"""
import os, time, json
import mujoco
xml = '''<mujoco><worldbody><light pos="0 0 3"/><geom type="plane" size="1 1 .1"/>
<body pos="0 0 .2"><freejoint/><geom type="box" size=".05 .05 .05" rgba="1 0 0 1"/></body></worldbody></mujoco>'''
m = mujoco.MjModel.from_xml_string(xml)
d = mujoco.MjData(m)
r = mujoco.Renderer(m, 480, 640)
mujoco.mj_forward(m, d)
r.update_scene(d); img = r.render()
renderer = vendor = "?"
try:  # 描画のコンテキストが有効なうちに、どの実装で描いているかを読む（NVIDIA か llvmpipe などのソフトウェアか）
    r._gl_context.make_current()
    from OpenGL import GL
    renderer = GL.glGetString(GL.GL_RENDERER).decode()
    vendor = GL.glGetString(GL.GL_VENDOR).decode()
except Exception as e:
    renderer = "unknown (" + repr(e)[:80] + ")"
n = 60
t = time.time()
for _ in range(n):
    mujoco.mj_step(m, d)
    r.update_scene(d)
    img = r.render()
fps = n / (time.time() - t)
import OpenGL
print(json.dumps({"ok": True, "fps": round(fps, 1), "mean_pixel": float(img.mean()),
                  "gl_renderer": renderer, "gl_vendor": vendor,
                  "mujoco": mujoco.__version__, "pyopengl": OpenGL.__version__}))
"""


def probe(backend: str, timeout: float) -> dict:
    env = dict(os.environ, MUJOCO_GL=backend, PYOPENGL_PLATFORM=backend)
    try:
        res = subprocess.run([sys.executable, "-c", PROBE], env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout after {timeout}s"}
    lines = [ln for ln in res.stdout.splitlines() if ln.startswith("{")]
    if res.returncode == 0 and lines:
        out = json.loads(lines[-1])
        if out["mean_pixel"] <= 0:  # 真っ黒なら描けていない
            out.update(ok=False, error="rendered image is black")
        return out
    return {"ok": False, "error": (res.stderr or res.stdout).strip().splitlines()[-1:] or ["unknown"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", nargs="+", default=["egl", "osmesa"])
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--timeout", type=float, default=120)
    args = ap.parse_args()
    results = {}
    chosen = None
    for backend in args.order:
        results[backend] = probe(backend, args.timeout)
        print(f"{backend:7s} -> {results[backend]}", flush=True)
        if results[backend]["ok"] and chosen is None:
            chosen = backend
    if chosen == "egl" and "llvmpipe" in str(results["egl"].get("gl_renderer", "")).lower():
        print("note: EGL works but uses the software renderer (llvmpipe), not the GPU", flush=True)
    report = {"chosen": chosen, "results": results}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2))
    if chosen is None:
        print("NO_BACKEND")
        sys.exit(1)
    print(f"CHOSEN={chosen}")


if __name__ == "__main__":
    main()
