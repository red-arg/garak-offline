"""Minimal stand-in for a LiteLLM proxy: OpenAI-compatible chat completions, bearer-key auth.

Usage: python3 mock_litellm.py <port> <api-key> [bind-host]
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, KEY = int(sys.argv[1]), sys.argv[2]
HOST = sys.argv[3] if len(sys.argv) > 3 else "127.0.0.1"
REPLY = "I'm sorry, but I can't help with that request."
stats = {"ok": 0, "unauthorized": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/stats"):
            self._send(200, stats)
        elif self.path.rstrip("/").endswith("/models"):
            self._send(200, {"object": "list", "data": [{"id": "mock-model", "object": "model"}]})
        else:
            self._send(200, {"status": "ok"})

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.headers.get("Authorization") != f"Bearer {KEY}":
            stats["unauthorized"] += 1
            self._send(401, {"error": {"message": "invalid api key", "type": "auth_error"}})
            return
        stats["ok"] += 1
        n = int(body.get("n") or 1)
        self._send(
            200,
            {
                "id": f"chatcmpl-{stats['ok']}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", "mock-model"),
                "choices": [
                    {
                        "index": i,
                        "message": {"role": "assistant", "content": REPLY},
                        "finish_reason": "stop",
                    }
                    for i in range(n)
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            },
        )


ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
