#!/usr/bin/env python3
"""Serve the local MicNow device laboratory, including the shared agent/Web bridge."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import signal
import sys
import tempfile
import threading
from urllib.parse import urlsplit

from device_bridge import Bridge, BridgeError
from device_sim import valid_shortcut

SKILL = Path(__file__).resolve().parent.parent
ASSETS = SKILL / "assets" / "device-lab"
STATIC = {"/": (ASSETS / "index.html", "text/html; charset=utf-8"),
          "/index.html": (ASSETS / "index.html", "text/html; charset=utf-8"),
          "/app.js": (ASSETS / "app.js", "text/javascript; charset=utf-8"),
          "/style.css": (ASSETS / "style.css", "text/css; charset=utf-8"),
          "/icon.svg": (ASSETS / "icon.svg", "image/svg+xml"),
          "/device-hero.png": (ASSETS / "device-hero.png", "image/png"),
          "/typeless.png": (ASSETS / "typeless.png", "image/png"),
          "/codex.svg": (ASSETS / "codex.svg", "image/svg+xml"),
          "/workbuddy.jpg": (ASSETS / "workbuddy.jpg", "image/jpeg"),
          "/claude.svg": (ASSETS / "claude.svg", "image/svg+xml"),
          "/docs/protocol.md": (SKILL / "references" / "minimum-protocol.md", "text/markdown; charset=utf-8"),
          "/docs/hardware-questions.md": (SKILL / "references" / "hardware-questions.md", "text/markdown; charset=utf-8")}


class RequestError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class LabServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port=0, known_shortcut=None):
        self.lock = threading.RLock()
        self.token = secrets.token_urlsafe(32)
        self.known_shortcut = known_shortcut
        self.bridge = Bridge(known_shortcut)
        try:
            super().__init__(("127.0.0.1", port), Handler)
        except BaseException:
            self.bridge.close()
            raise
        self.runtime = Path(tempfile.mkdtemp(prefix="micnow-device-lab-"))
        self.connection_file = self.runtime / "connection.json"
        self.url = "http://127.0.0.1:" + str(self.server_address[1])
        descriptor = os.open(str(self.connection_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({"format": "micnow-lab-connection/0.4", "url": self.url,
                       "token": self.token, "pid": os.getpid()}, stream)

    def envelope(self, result=None):
        state = self.bridge.state()
        return {"ok": True if result is None else result.get("ok", False),
                "result": result, "token": self.token, "state": state,
                "connection_file": str(self.connection_file),
                "client_script": str(Path(__file__).with_name("device_client.py")),
                "simulation": True}

    def cleanup(self):
        self.bridge.close()
        self.connection_file.unlink(missing_ok=True)
        try:
            self.runtime.rmdir()
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    server_version = "MicNowLocal/0.4"

    def log_message(self, *_args):
        pass

    def check_source(self):
        port = self.server.server_address[1]
        hosts = {"127.0.0.1:" + str(port), "localhost:" + str(port)}
        if self.headers.get("Host") not in hosts:
            raise RequestError(403, "INVALID_HOST", "仅允许本地页面访问。")
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {"http://" + host for host in hosts}:
            raise RequestError(403, "INVALID_ORIGIN", "仅允许本地页面访问。")
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            raise RequestError(403, "CROSS_SITE_REQUEST", "不接受跨站请求。")

    def write(self, status, content, kind="application/json; charset=utf-8"):
        raw = content if isinstance(content, bytes) else json.dumps(content, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(raw)

    def fail(self, error):
        self.write(getattr(error, "status", 400), {"ok": False, "simulation": True,
                                                 "error": {"code": getattr(error, "code", "LOCAL_ERROR"),
                                                           "message": str(error)}})

    def do_GET(self):
        try:
            self.check_source()
            path = urlsplit(self.path).path
            if path == "/api/state":
                with self.server.lock:
                    self.write(200, self.server.envelope())
            elif path in STATIC:
                asset, kind = STATIC[path]
                if not asset.is_file() or asset.is_symlink():
                    raise RequestError(404, "ASSET_NOT_FOUND", "此本地资源尚未准备好。")
                self.write(200, asset.read_bytes(), kind)
            else:
                raise RequestError(404, "NOT_FOUND", "未找到此本地资源。")
        except (RequestError, BridgeError, OSError) as error:
            self.fail(error)

    def body(self):
        self.check_source()
        token = self.headers.get("X-MicNow-Token", "")
        if not secrets.compare_digest(token.encode("utf-8"), self.server.token.encode("ascii")):
            raise RequestError(403, "INVALID_TOKEN", "请刷新本地页面后重试。")
        if self.headers.get_content_type() != "application/json":
            raise RequestError(400, "INVALID_CONTENT_TYPE", "请求应为 JSON。")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not 0 < length <= 8192:
            raise RequestError(400, "INVALID_BODY_SIZE", "请求大小无效。")
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeError):
            raise RequestError(400, "INVALID_JSON", "请求格式无效。")
        if not isinstance(data, dict):
            raise RequestError(400, "INVALID_ARGUMENT", "请求必须是对象。")
        return data

    def do_POST(self):
        try:
            data = self.body()
            path = urlsplit(self.path).path
            source = data.get("source", "web")
            Bridge.validate_source(source)
            request_id = data.get("id")
            if request_id is not None and (not isinstance(request_id, str) or not 0 < len(request_id) <= 96):
                raise RequestError(400, "INVALID_ID", "请求 ID 无效。")
            with self.server.lock:
                if path == "/api/command":
                    if set(data) - {"id", "command", "args", "source"} or not isinstance(data.get("command"), str):
                        raise RequestError(400, "INVALID_ARGUMENT", "命令字段无效。")
                    result = self.server.bridge.command(data["command"], data.get("args", {}), source, request_id)
                elif path == "/api/setup":
                    if set(data) - {"id", "source", "shortcut", "speak_mode", "target_app"}:
                        raise RequestError(400, "INVALID_ARGUMENT", "设置字段无效。")
                    result = self.server.bridge.setup({k: v for k, v in data.items() if k not in ("id", "source")}, source, request_id)
                elif path == "/api/reset":
                    if set(data) - {"source"}:
                        raise RequestError(400, "INVALID_ARGUMENT", "重置不接受额外参数。")
                    self.server.bridge.close()
                    self.server.bridge = Bridge(self.server.known_shortcut)
                    result = {"ok": True, "result": {"reset": True}}
                elif path == "/api/shutdown":
                    if set(data) - {"source"}:
                        raise RequestError(400, "INVALID_ARGUMENT", "关闭不接受额外参数。")
                    self.write(200, {"ok": True, "simulation": True, "result": {"stopping": True}})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                else:
                    raise RequestError(404, "NOT_FOUND", "未找到此本地操作。")
                self.write(200, self.server.envelope(result))
        except (RequestError, BridgeError, OSError) as error:
            self.fail(error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--known-shortcut")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be 0–65535")
    if args.known_shortcut is not None and not valid_shortcut(args.known_shortcut):
        parser.error("invalid known shortcut")
    server = LabServer(args.port, args.known_shortcut)
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
    print(json.dumps({"url": server.url + "/", "port": server.server_address[1],
                      "connection_file": str(server.connection_file),
                      "transport": server.bridge.transport.kind, "simulation": True}, ensure_ascii=False), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.cleanup()


if __name__ == "__main__":
    main()
