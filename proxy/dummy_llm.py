"""試運転用の、決まった回答を返す OpenAI 互換サーバー（GPU もモデルも要らない）。

- 最初の呼び出し: タスク（プロンプトの文面から判定）に合わせた短いコードを返す。
  物体の位置を読んで、つかむ位置の上まで腕を動かすだけなので、課題は成功しない。
- 複数ターンの判断の呼び出し（"The following code blocks were just executed" を含む）:
  1回目は REGENERATE と書き直したコード、2回目以降は FINISH を返す。
  これで「書き直し → 実行 → 終了」の流れが最後まで通るかを確かめる。

  python proxy/dummy_llm.py --port 8000
"""

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MT_MARK = "The following code blocks were just executed"

CODE = {
    "stack": """import numpy as np
red, _, red_ext = get_object_pose("red cube", return_bbox_extent=True)
green, _, green_ext = get_object_pose("green cube", return_bbox_extent=True)
print("red", red, "green", green)
p, q = sample_grasp_pose("red cube")
open_gripper()
goto_pose(np.asarray(p) + np.array([0, 0, 0.15]), q)
""",
    "nut": """import numpy as np
nut_p, nut_q = get_object_pose("white hollow center of the brown square nut")
p, q = sample_grasp_pose("extruded handle of the brown square nut")
print("nut", nut_p, "handle", p)
open_gripper()
goto_pose(np.asarray(p) + np.array([0, 0, 0.15]), q)
""",
    "handover": """import numpy as np
h, _ = get_hammer_pose()
print("hammer", h)
open_gripper_arm0()
goto_pose_arm0(np.asarray(h) + np.array([0, 0, 0.15]), np.array([0, 0.707, 0.707, 0]))
""",
}


def detect_task(text: str) -> str:
    # 見本（skill）に他タスクの言葉が出てくるので、タスク文の Goal 行だけで判定する
    goal = next((ln for ln in text.splitlines() if ln.startswith("Goal:")), text)
    if "hammer" in goal:
        return "handover"
    if "brown square nut" in goal:
        return "nut"
    return "stack"


def all_text(messages: list[dict]) -> str:
    out = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            out.append(c)
        elif isinstance(c, list):
            out += [p.get("text", "") for p in c if isinstance(p, dict)]
    return "\n".join(out)


def answer(messages: list[dict]) -> str:
    text = all_text(messages)
    task = detect_task(text)
    if MT_MARK not in text:
        return "```python\n# dummy turn 1\n" + CODE[task] + "```"
    if "# dummy turn 2" in text:
        return "FINISH"
    return "REGENERATE\n```python\n# dummy turn 2\n" + CODE[task] + 'print("regenerated")\n```'


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _send(self, status: int, obj: dict) -> None:
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/v1/models"):
            self._send(200, {"object": "list", "data": [{"id": ARGS.model, "object": "model"}]})
        else:
            self._send(200, {"ok": True})

    def do_POST(self) -> None:
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        content = answer(req.get("messages", []))
        n_in = len(all_text(req.get("messages", []))) // 4
        self._send(200, {
            "id": f"dummy-{time.time_ns()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.get("model", ARGS.model),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": n_in, "completion_tokens": len(content) // 4,
                      "total_tokens": n_in + len(content) // 4},
        })


def main() -> None:
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--model", default="dummy")
    ARGS = ap.parse_args()
    print(f"dummy LLM on :{ARGS.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
