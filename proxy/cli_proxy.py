"""Claude Code / Codex CLI を OpenAI 互換の /chat/completions として見せる中継サーバー。

CaP-X は LLM を OpenAI 互換の HTTP で呼ぶ。サブスクリプションで使える CLI
（`claude -p` と `codex exec`）をその口に差し込むために使う。

モデル名の書き方:
  claude-cli/<model>[@<effort>] 例: claude-cli/claude-opus-5-5@medium
  codex-cli/<model>[@<effort>]  例: codex-cli/gpt-6-sol@low
  agy-cli/<model>               例: agy-cli/gemini-3.8-flash-low（Antigravity CLI）
  replay-cli/<name>             例: replay-cli/claude-fable-5-1@medium
    replay/<name>/<プロンプトの sha256 先頭16桁>/responses/*.json に作っておいた回答を順に返す。
    回答が無いプロンプトは prompt.txt に書き出し、何もしないコードを返す（その試行は失敗扱い）。
    手元で呼べないモデル（クラウドでしか使えない Fable）の1回で答える条件に使う。
    回答は scripts/gen_replay.py で、claude-cli と同じ引数の claude -p から作る。

CLI にはツールを使わせない（Claude は --tools ""、Codex は read-only sandbox と
空の作業フォルダ）。呼び出しごとに logs/proxy_calls.jsonl へ所要時間などを残す。

Codex は既定（--codex-home clean）で、認証ファイルだけをリンクした専用の CODEX_HOME を使う。
~/.codex のままだと、個人ルール（AGENTS.md）・メモリ・プラグイン・MCP サーバーが毎回
文脈に入る（1回あたり約1.5万トークン）。Claude を --system-prompt と --setting-sources "" で
素の状態にしているのに合わせ、組み込みの指示文も SYSTEM_PROMPT に置き換え、ツールも切る。
--codex-home user で以前（2026-10-31 の本番 runs/main）と同じ ~/.codex を使う。

起動:
  python proxy/cli_proxy.py --port 8120
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import tempfile
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SYSTEM_PROMPT = (
    "You are a code-generation backend for a robot-control benchmark. "
    "Answer only with the text the user asks for. Do not run tools or commands."
)
CALL_TIMEOUT_S = 600
CLEAN_CODEX_HOME = Path.home() / ".cache" / "pai-final" / "codex-home"
# 専用 CODEX_HOME の config.toml。{instructions} は SYSTEM_PROMPT を書いたファイル。
CLEAN_CODEX_CONFIG = """\
# PAI 最終課題のベンチマーク用（proxy/cli_proxy.py が書き出す）。
# Claude（--system-prompt、ツールなし）とできるだけ同じ条件にする。
model_instructions_file = "{instructions}"
[tools]
web_search = false
[features]
memories = false
shell_tool = false
unified_exec = false
apps = false
plugins = false
remote_plugin = false
hooks = false
multi_agent = false
goals = false
image_generation = false
view_image = false
sleep_tool = false
tool_suggest = false
skill_search = false
skill_mcp_dependency_install = false
code_mode_host = false
computer_use = false
browser_use = false
browser_use_external = false
shell_snapshot = false
"""
_CODEX_ENV: dict[str, str] | None = None  # None なら親の環境のまま（~/.codex）

app = FastAPI()
LOG_PATH = Path(__file__).resolve().parent.parent / "logs" / "proxy_calls.jsonl"
# CLI ごとの同時実行数（サブスクの回数制限に配慮して小さめ）
_SEMAPHORES: dict[str, asyncio.Semaphore] = {}
MAX_PARALLEL = {"claude-cli": 4, "codex-cli": 4, "agy-cli": 4, "replay-cli": 4}
REPLAY_ROOT = Path(__file__).resolve().parent.parent / "replay"
_REPLAY_NEXT: dict[str, int] = {}  # プロンプトごとに次に返す回答の番号


class ChatRequest(BaseModel):
    model: str
    messages: list[dict]
    temperature: float | None = None
    max_tokens: int | None = None


def _flatten(messages: list[dict]) -> str:
    """OpenAI 形式の messages を、役割の見出し付きの1つの文章にする。"""
    parts = []
    for m in messages:
        content = m.get("content")
        if isinstance(content, list):
            texts = []
            for item in content:
                if item.get("type") == "text":
                    texts.append(item.get("text") or "")
                else:
                    texts.append("[image omitted]")
            content = "\n".join(texts)
        parts.append(f"### {m.get('role', 'user').upper()}\n{content or ''}")
    if len(messages) > 1:
        parts.append("### ASSISTANT\n(Write your reply to the last message.)")
    return "\n\n".join(parts)


def prepare_clean_codex_home(home: Path = CLEAN_CODEX_HOME) -> dict[str, str]:
    """認証ファイルへのリンクと、余計なものを切った config.toml だけの CODEX_HOME を作る。"""
    home.mkdir(parents=True, exist_ok=True)
    auth = home / "auth.json"
    if not auth.exists():
        auth.symlink_to(Path.home() / ".codex" / "auth.json")
    instructions = home / "instructions.md"
    instructions.write_text(SYSTEM_PROMPT + "\n")
    (home / "config.toml").write_text(CLEAN_CODEX_CONFIG.format(instructions=instructions))
    return {**os.environ, "CODEX_HOME": str(home)}


async def _run(cmd: list[str], prompt: str, cwd: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(prompt.encode()), CALL_TIMEOUT_S)
    except asyncio.TimeoutError:
        proc.kill()
        raise
    return proc.returncode, out.decode(errors="replace"), err.decode(errors="replace")


async def _call_claude(model: str, prompt: str, workdir: str) -> tuple[str, dict]:
    effort = None
    if "@" in model:
        model, effort = model.split("@", 1)
    cmd = [
        "claude", "-p", "--model", model,
        *(["--effort", effort] if effort else []),
        "--tools", "",
        "--strict-mcp-config", "--setting-sources", "",
        "--no-session-persistence",
        "--system-prompt", SYSTEM_PROMPT,
        "--output-format", "json",
    ]
    rc, out, err = await _run(cmd, prompt, workdir)
    try:
        body = json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(f"claude rc={rc} stdout={out[-500:]} stderr={err[-500:]}") from exc
    if body.get("is_error"):
        raise RuntimeError(f"claude error: {body.get('result')}")
    usage = body.get("usage", {})
    return body.get("result", ""), {
        "input_tokens": usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }


async def _call_codex(model: str, prompt: str, workdir: str) -> tuple[str, dict]:
    effort = None
    if "@" in model:
        model, effort = model.split("@", 1)
    out_file = os.path.join(workdir, "last_message.txt")
    cmd = [
        "codex", "exec", "-m", model,
        "-s", "read-only", "--skip-git-repo-check", "--ephemeral",
        "-C", workdir, "-o", out_file,
    ]
    if effort:
        cmd += ["-c", f"model_reasoning_effort={effort}"]
    cmd.append("-")
    rc, out, err = await _run(cmd, SYSTEM_PROMPT + "\n\n" + prompt, workdir, _CODEX_ENV)
    if not os.path.exists(out_file):
        raise RuntimeError(f"codex rc={rc} stderr={err[-800:]}")
    text = Path(out_file).read_text()
    return text, {}


async def _call_agy(model: str, prompt: str, workdir: str) -> tuple[str, dict]:
    cmd = [
        "agy", "-p", SYSTEM_PROMPT + "\n\n" + prompt,
        "--model", model,
        "--sandbox", "--disable-slash-commands",
        "--output-format", "json",
        "--print-timeout", f"{CALL_TIMEOUT_S - 30}s",
    ]
    rc, out, err = await _run(cmd, "", workdir)
    try:
        body = json.loads(out.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(f"agy rc={rc} stdout={out[-500:]} stderr={err[-500:]}") from exc
    if body.get("status") != "SUCCESS":
        raise RuntimeError(f"agy status={body.get('status')} body={str(body)[:500]}")
    usage = body.get("usage", {})
    return body.get("response", ""), {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0) + usage.get("thinking_tokens", 0),
    }


def prompt_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def _call_replay(name: str, prompt: str) -> tuple[str, dict]:
    key = prompt_key(prompt)
    d = REPLAY_ROOT / name.replace("/", "_") / key
    files = sorted((d / "responses").glob("*.json"))
    if not files:
        d.mkdir(parents=True, exist_ok=True)
        (d / "prompt.txt").write_text(prompt)
        return "```python\npass\n```", {"replay_key": key, "replay_missing": True}
    i = _REPLAY_NEXT.get(key, 0)
    _REPLAY_NEXT[key] = i + 1
    rec = json.loads(files[i % len(files)].read_text())
    # 回答の数より多く呼ばれたら最初から使い回す（ログの replay_reused で分かる）
    return rec["text"], {"replay_key": key, "replay_index": i % len(files), "replay_reused": i >= len(files)}


@app.post("/chat/completions")
async def chat(req: ChatRequest):
    backend, _, model = req.model.partition("/")
    if backend not in MAX_PARALLEL or not model:
        raise HTTPException(400, f"unknown model {req.model!r}; use claude-cli/, codex-cli/, agy-cli/ or replay-cli/")
    sem = _SEMAPHORES.setdefault(backend, asyncio.Semaphore(MAX_PARALLEL[backend]))
    prompt = _flatten(req.messages)
    start = time.time()
    status, usage, text, error = "ok", {}, "", None
    async with sem:
        with tempfile.TemporaryDirectory(prefix="capx_cli_") as workdir:
            try:
                if backend == "claude-cli":
                    text, usage = await _call_claude(model, prompt, workdir)
                elif backend == "replay-cli":
                    text, usage = _call_replay(model, prompt)
                elif backend == "agy-cli":
                    text, usage = await _call_agy(model, prompt, workdir)
                else:
                    text, usage = await _call_codex(model, prompt, workdir)
            except Exception as exc:  # noqa: BLE001 - ログに残して 502 で返す
                status, error = "error", f"{type(exc).__name__}: {exc}"
    record = {
        "time": start,
        "model": req.model,
        "latency_s": round(time.time() - start, 2),
        "prompt_chars": len(prompt),
        "response_chars": len(text),
        "status": status,
        "error": error,
        **usage,
    }
    if backend == "codex-cli":
        record["codex_home"] = "user" if _CODEX_ENV is None else "clean"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if status != "ok":
        # CaP-X は 5xx なら待って再試行する
        raise HTTPException(502, error)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(start),
        "model": req.model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}
        ],
        "usage": {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8120)
    parser.add_argument("--codex-home", choices=["clean", "user"], default="clean",
                        help="clean: 専用の CODEX_HOME（既定）、user: ~/.codex のまま")
    args = parser.parse_args()
    if args.codex_home == "clean":
        _CODEX_ENV = prepare_clean_codex_home()
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
