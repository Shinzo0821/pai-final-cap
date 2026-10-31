"""CaP-X と OpenAI 互換サーバー（vLLM など）の間に入り、呼び出しをそのまま中継して記録する。

CaP-X（run_grid.py）は http://127.0.0.1:8120/chat/completions に POST する。
このプロキシはそれを --upstream（既定 http://127.0.0.1:8000/v1/chat/completions）へそのまま送り、
1回ごとに要求（model・messages・temperature・max_tokens）と応答（本文・usage・所要時間）を
JSON Lines で --log に追記する。中身は変えない（--force-no-think を付けたときだけ
chat_template_kwargs に enable_thinking=false を足す。vLLM の既定で切れない場合の予備）。

標準ライブラリだけで動く。
  python proxy/log_proxy.py --port 8120 --upstream http://127.0.0.1:8000/v1/chat/completions --log logs/llm_calls.jsonl
"""

from __future__ import annotations

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOCK = threading.Lock()
ARGS: argparse.Namespace


def _append(rec: dict) -> None:
    with LOCK, open(ARGS.log, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # 標準エラーへのアクセスログは出さない
        pass

    def _send(self, status: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("/health", "/healthz"):
            self._send(200, b'{"ok": true}')
        else:
            self._send(404, b'{"error": "not found"}')

    def do_POST(self) -> None:
        if not self.path.rstrip("/").endswith("chat/completions"):
            self._send(404, b'{"error": "only /chat/completions is proxied"}')
            return
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        try:
            req = json.loads(raw)
        except json.JSONDecodeError:
            self._send(400, b'{"error": "bad json"}')
            return
        if ARGS.force_no_think:
            kw = dict(req.get("chat_template_kwargs") or {})
            kw.setdefault("enable_thinking", False)
            req["chat_template_kwargs"] = kw
        if ARGS.model:  # CaP-X の --model と vLLM の served-model-name が違うときだけ
            req["model"] = ARGS.model
        body = json.dumps(req).encode()
        start = time.time()
        status, out = 502, b""
        err = None
        try:
            r = urllib.request.urlopen(
                urllib.request.Request(ARGS.upstream, data=body, headers={"Content-Type": "application/json"}),
                timeout=ARGS.timeout,
            )
            status, out = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, out = e.code, e.read()
            err = out.decode(errors="replace")[:2000]
        except Exception as e:  # noqa: BLE001  接続できない・時間切れ
            err = repr(e)
            out = json.dumps({"error": err}).encode()
        elapsed = round(time.time() - start, 3)

        # time・model・status・latency_s・response_chars・output_tokens は scripts/analyze.py の集計と同じ名前
        rec = {
            "time": round(start, 3),
            "model": req.get("model"),
            "latency_s": elapsed,
            "http_status": status,
            "status": "ok" if status == 200 else "error",
            "request": {k: req.get(k) for k in ("model", "temperature", "max_tokens", "chat_template_kwargs") if k in req},
            "messages": req.get("messages"),
        }
        if err:
            rec["error"] = err
        else:
            try:
                resp = json.loads(out)
                choice = (resp.get("choices") or [{}])[0]
                msg = choice.get("message") or {}
                content = msg.get("content") or ""
                usage = resp.get("usage") or {}
                rec.update({
                    "response_chars": len(content),
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "content": content,
                    "reasoning": msg.get("reasoning") or msg.get("reasoning_content"),
                    "finish_reason": choice.get("finish_reason"),
                    "has_think_tag": "<think>" in content or "</think>" in content,
                })
            except (json.JSONDecodeError, AttributeError, IndexError):
                rec["status"] = "error"
                rec["raw_response"] = out.decode(errors="replace")[:2000]
        _append(rec)
        self._send(status, out)


def main() -> None:
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8120)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--upstream", default="http://127.0.0.1:8000/v1/chat/completions")
    ap.add_argument("--log", default="logs/llm_calls.jsonl")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--model", default=None, help="上流に送る model 名を固定する（省略時はそのまま）")
    ap.add_argument("--force-no-think", action="store_true",
                    help="要求に chat_template_kwargs.enable_thinking=false を足す（予備）")
    ARGS = ap.parse_args()
    Path(ARGS.log).parent.mkdir(parents=True, exist_ok=True)
    srv = ThreadingHTTPServer((ARGS.host, ARGS.port), Handler)
    print(f"log proxy :{ARGS.port} -> {ARGS.upstream}  (log: {ARGS.log})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
