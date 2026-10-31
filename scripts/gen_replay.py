"""replay/<name>/*/prompt.txt それぞれに、claude -p で回答を N 個作る（Fable などクラウドでしか呼べないモデル用）。

  python scripts/gen_replay.py --name claude-fable-5-1@medium --n 10

呼び方は proxy/cli_proxy.py の claude-cli と同じ（_call_claude をそのまま使う。ツールなし、
--system-prompt、--setting-sources ""、--effort）。できた回答は replay/<name>/<key>/responses/NN.json。
すでにある番号は作り直さないので、途中で止まっても同じコマンドで続きから作れる。
必要なもの: claude CLI と、fastapi・uvicorn・pydantic（cli_proxy の import に要る）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "proxy"))
from cli_proxy import REPLAY_ROOT, _call_claude, prompt_key  # noqa: E402


async def one(sem: asyncio.Semaphore, name: str, prompt: str, out: Path, cli_version: str) -> None:
    async with sem:
        for attempt in range(3):
            start = time.time()
            try:
                with tempfile.TemporaryDirectory(prefix="capx_cli_") as wd:
                    text, usage = await _call_claude(name, prompt, wd)
            except Exception as exc:  # noqa: BLE001
                print(f"  {out.parent.parent.name}/{out.name} attempt {attempt + 1} failed: {exc}", flush=True)
                await asyncio.sleep(30)
                continue
            rec = {"text": text, "model": name, "latency_s": round(time.time() - start, 2), "time": start,
                   "claude_cli": cli_version, **usage}
            out.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
            print(f"  {out.parent.parent.name}/{out.name} ok ({rec['latency_s']}s, {len(text)} chars)", flush=True)
            return
        print(f"  {out.parent.parent.name}/{out.name} gave up", flush=True)


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="claude のモデル名（@effort 付き可）。replay/<name>/ を読む")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--parallel", type=int, default=4)
    args = ap.parse_args()
    cli_version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    sem = asyncio.Semaphore(args.parallel)
    tasks = []
    for prompt_file in sorted((REPLAY_ROOT / args.name.replace("/", "_")).glob("*/prompt.txt")):
        prompt = prompt_file.read_text()
        assert prompt_key(prompt) == prompt_file.parent.name, f"prompt.txt が書き換わっている: {prompt_file}"
        resp_dir = prompt_file.parent / "responses"
        resp_dir.mkdir(exist_ok=True)
        for i in range(args.n):
            out = resp_dir / f"{i:02d}.json"
            if not out.exists():
                tasks.append(one(sem, args.name, prompt, out, cli_version))
    print(f"{len(tasks)} calls to make ({cli_version})", flush=True)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
