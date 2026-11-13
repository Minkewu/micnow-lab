#!/usr/bin/env python3
"""Single-owner local bridge, talking real JSONL bytes to a simulated device."""
import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import uuid
from collections import OrderedDict

from device_sim import PROTOCOL, MAX_FRAME, SCENARIOS, valid_shortcut


class BridgeError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


class DeviceTransport:
    def __init__(self):
        self.queue = queue.Queue()
        self.closed = False
        self.kind = "pipe"
        self.endpoint = "local-child-process"
        self.process = None
        self.read_fd = self.write_fd = None
        try:
            import pty
            import tty
            master, slave = pty.openpty()
            tty.setraw(slave)
            self.endpoint = os.ttyname(slave)
            try:
                self.process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).with_name("device_sim.py"))],
                                                stdin=slave, stdout=slave, stderr=subprocess.DEVNULL, close_fds=True)
            finally:
                os.close(slave)
            self.read_fd = self.write_fd = master
            self.kind = "pty"
        except (ImportError, OSError):
            if self.process is not None:
                raise
            self.process = subprocess.Popen([sys.executable, "-u", str(Path(__file__).with_name("device_sim.py"))],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                            stderr=subprocess.DEVNULL, bufsize=0)
            self.read_fd = self.process.stdout.fileno()
            self.write_fd = self.process.stdin.fileno()
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

    def _reader(self):
        pending = b""
        try:
            while not self.closed:
                data = os.read(self.read_fd, 4096)
                if not data:
                    break
                pending += data
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    if len(line) > MAX_FRAME:
                        raise ValueError("oversize frame")
                    self.queue.put(json.loads(line))
                if len(pending) > MAX_FRAME:
                    break
        except (OSError, ValueError, UnicodeError):
            pass
        finally:
            self.queue.put(None)

    def exchange(self, frame, timeout=0.7):
        if self.closed or self.process.poll() is not None:
            raise BridgeError("TRANSPORT_CLOSED", "模拟设备进程已停止，请重新开始。")
        raw = json.dumps(frame, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
        if len(raw) > MAX_FRAME:
            raise BridgeError("FRAME_TOO_LARGE", "命令超过模拟协议长度限制。")
        try:
            offset = 0
            while offset < len(raw):
                offset += os.write(self.write_fd, raw[offset:])
        except OSError as error:
            raise BridgeError("TRANSPORT_CLOSED", "模拟连接已关闭。") from error
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                response = self.queue.get(timeout=max(0, end - time.monotonic()))
            except queue.Empty:
                break
            if response is None:
                raise BridgeError("TRANSPORT_CLOSED", "模拟设备进程已停止。")
            if (isinstance(response, dict) and response.get("id") == frame["id"]
                    and response.get("protocol") == PROTOCOL):
                return response
        raise BridgeError("RESPONSE_TIMEOUT", "未收到模拟设备回执，结果待回读确认。")

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        if self.kind == "pty":
            os.close(self.read_fd)
        else:
            self.process.stdin.close()
            self.process.stdout.close()


class Bridge:
    def __init__(self, known_shortcut=None):
        self.lock = threading.RLock()
        self.known_shortcut = known_shortcut
        self.initial_shortcut_pending = known_shortcut is not None
        self.transport = DeviceTransport()
        self.commands = []
        self.setups = OrderedDict()
        self.verified_revision = None
        self.desired = None
        self.trial = None
        self.phase = "idle"
        self.message = "模拟设备已就绪，选择自己设置或让 AI 帮忙。"
        self.steps = []
        self.snapshot = None
        self.refresh()

    def close(self):
        with self.lock:
            self.transport.close()

    def _call(self, command, args=None, source="web", request_id=None, record=True):
        frame = {"protocol": PROTOCOL, "id": request_id or str(uuid.uuid4()),
                 "command": command, "args": args or {}}
        start = time.monotonic()
        try:
            result = self.transport.exchange(frame)
        except BridgeError as error:
            result = {"protocol": PROTOCOL, "id": frame["id"], "ok": False,
                      "error": {"code": error.code, "message": error.message},
                      "outcome": "unknown" if error.code == "RESPONSE_TIMEOUT" else "not-executed",
                      "simulation": True}
        if record:
            error = result.get("error", {})
            self.commands.append({"request_id": frame["id"], "command": command,
                                  "source": source, "ok": result["ok"],
                                  "status": "ok" if result["ok"] else error.get("code", "error"),
                                  "message": "模拟设备已回执" if result["ok"] else error.get("message", "操作未完成"),
                                  "at": time.time(), "roundtrip_ms": round((time.monotonic() - start) * 1000, 1),
                                  "transport_io": True, "request": frame, "response": copy.deepcopy(result)})
            self.commands = self.commands[-80:]
        return result

    def refresh(self):
        result = self._call("lab.snapshot", record=False)
        if result["ok"]:
            fresh = result["result"]
            if (self.snapshot and (fresh["revision"] != self.snapshot["revision"]
                                 or fresh["scenario"] != self.snapshot["scenario"]
                                 or fresh["connection"] != self.snapshot["connection"])):
                self.verified_revision = None
                self.trial = None
            self.snapshot = fresh
        elif self.snapshot:
            self.snapshot["connection"]["connected"] = False
            self.snapshot["speak"] = {"pressed": False, "active": False, "light": "off"}
            self.verified_revision = None
            self.trial = None
            self.phase = "waiting-connection"
            self.message = result["error"]["message"]
        else:
            raise BridgeError("START_FAILED", "模拟设备未能启动。")

    def state(self, refresh=True):
        with self.lock:
            if refresh:
                self.refresh()
            data = copy.deepcopy(self.snapshot)
            connection = data["connection"]
            connection.update({"transport": self.transport.kind,
                               "label": "虚拟串口 · PTY" if self.transport.kind == "pty" else "本地进程管道",
                               "endpoint": self.transport.endpoint})
            verified = (self.verified_revision == data["revision"] and self.verified_revision is not None
                        and connection["connected"] and connection["permission"] != "required")
            phase, message = self.phase, self.message
            if not connection["connected"]:
                phase, message = "waiting-connection", "模拟麦克风未连接，请恢复连接后重新核验。"
            elif connection["permission"] == "required":
                phase, message = "waiting-permission", "需要你允许本次模拟连接。"
            elif verified and phase != "waiting-audio":
                phase = "ready" if self.trial else "waiting-trial"
                message = "配置与模拟试说已核验，可以继续体验。" if self.trial else "配置已回读核验，试按一次 Speak。"
            data.update({"verified_revision": self.verified_revision if verified else None,
                         "verification": {"config": verified, "trial": bool(verified and self.trial)},
                         "trial": copy.deepcopy(self.trial), "commands": copy.deepcopy(self.commands),
                         "workflow": {"phase": phase, "message": message, "steps": copy.deepcopy(self.steps)},
                         "known_shortcut": self.known_shortcut,
                         "config_scope": {"device_candidates": ["shortcut", "speak_mode"],
                                          "host_metadata": ["target_app", "voice_tool"]}})
            return data

    def _verify(self, expected, source, request_id=None):
        if not isinstance(expected, dict) or set(expected) != set(self.snapshot["config"]):
            return {"ok": False, "error": {"code": "EXPECTED_CONFIG_REQUIRED", "message": "需要完整的目标配置才能核验。"}}
        result = self._call("config.get", source=source, request_id=request_id)
        self.refresh()
        if not result["ok"]:
            self.verified_revision = None
            return result
        data = result["result"]
        if data["config"] != expected:
            self.verified_revision = None
            self.trial = None
            self.phase, self.message = "blocked-readback", "回读结果与目标配置不同，已停止自动写入。"
            return {"ok": False, "error": {"code": "READBACK_MISMATCH", "message": self.message},
                    "expected": expected, "actual": data["config"], "revision": data["revision"]}
        self.verified_revision = data["revision"]
        self.desired = dict(expected)
        self.initial_shortcut_pending = False
        self.phase = "waiting-trial"
        return {"ok": True, "result": {"verified": True, "revision": data["revision"], "config": data["config"]}}

    @staticmethod
    def validate_source(source):
        if source not in ("web", "agent"):
            raise BridgeError("INVALID_SOURCE", "来源必须为 web 或 agent。")

    def command(self, command, args=None, source="agent", request_id=None):
        self.validate_source(source)
        if not isinstance(args if args is not None else {}, dict):
            raise BridgeError("INVALID_ARGUMENT", "args 必须是对象。")
        if command == "lab.snapshot":
            raise BridgeError("UNKNOWN_COMMAND", "请通过状态接口读取共享状态。")
        with self.lock:
            args = args or {}
            if command == "config.verify":
                if set(args) - {"expected_config"}:
                    raise BridgeError("INVALID_ARGUMENT", "核验参数无效。")
                return self._verify(args.get("expected_config", self.desired), source, request_id)
            if command in ("config.set", "lab.scenario", "lab.permission"):
                self.verified_revision = None
                self.trial = None
                self.phase, self.message = "idle", "设置已变化，需要重新回读核验。"
            if command == "config.set" and isinstance(args.get("patch"), dict):
                self.desired = dict(self.snapshot["config"], **args["patch"])
            if command == "speak.test" and self.verified_revision != self.snapshot["revision"]:
                return {"ok": False, "error": {"code": "CONFIG_NOT_VERIFIED", "message": "请先完成配置回读核验。"}}
            result = self._call(command, args, source, request_id)
            self.refresh()
            if (command == "config.set" and result["ok"]
                    and isinstance(args.get("patch"), dict) and "shortcut" in args["patch"]):
                # An explicit choice also wins when it matches the factory value
                # and therefore does not increment the device revision.
                self.initial_shortcut_pending = False
            if command == "speak.test":
                if result["ok"]:
                    self.trial = result["result"]
                    self.phase = "ready"
                else:
                    self.trial = None
                    self.phase, self.message = "waiting-audio", result.get("error", {}).get("message", "试说未通过。")
            return result

    def setup(self, data, source="agent", request_id=None):
        self.validate_source(source)
        allowed = {"shortcut", "speak_mode", "target_app"}
        if not isinstance(data, dict) or set(data) - allowed:
            raise BridgeError("INVALID_ARGUMENT", "配置参数无效。")
        if ("shortcut" in data and not valid_shortcut(data["shortcut"])) or (
                "speak_mode" in data and data["speak_mode"] not in ("hold", "toggle")) or (
                "target_app" in data and data["target_app"] not in ("codex", "workbuddy", "general")):
            raise BridgeError("INVALID_ARGUMENT", "配置参数值无效。")
        with self.lock:
            request_id = request_id or str(uuid.uuid4())
            fingerprint = json.dumps(data, sort_keys=True)
            if request_id in self.setups:
                old, result = self.setups[request_id]
                if old != fingerprint:
                    raise BridgeError("ID_CONFLICT", "同一配置请求 ID 不能用于不同内容。")
                self.refresh()
                if (result.get("ok") and (result.get("result", {}).get("revision") != self.snapshot["revision"]
                        or self.verified_revision != self.snapshot["revision"]
                        or not self.snapshot["connection"]["connected"]
                        or self.snapshot["connection"]["permission"] == "required")):
                    return {"ok": False, "error": {"code": "STALE_OPERATION",
                            "message": "此请求的结果已过期，请重新读取状态后发起新的配置请求。"}}
                return copy.deepcopy(result)
            self.refresh()
            self.steps = []
            self.verified_revision = None
            self.trial = None
            def call(command, args, label):
                key = hashlib.sha256((request_id + command).encode()).hexdigest()[:32]
                result = self._call(command, args, source, key)
                self.steps.append({"label": label, "status": "done" if result["ok"] else "error"})
                return result
            result = call("device.info", {}, "识别模拟设备")
            if not result["ok"]:
                return result
            result = call("device.capabilities", {}, "确认支持的功能")
            if not result["ok"]:
                return result
            supported = result["result"]["supported_apps"]
            result = call("config.get", {}, "读取当前配置")
            if not result["ok"]:
                return result
            current = result["result"]
            desired = dict(current["config"], **data)
            if (self.initial_shortcut_pending and current["revision"] == 0
                    and "shortcut" not in data):
                desired["shortcut"] = self.known_shortcut
            if desired["target_app"] not in supported:
                self.phase, self.message = "partial", "当前模拟环境尚未支持这个应用，未修改配置。"
                return {"ok": False, "error": {"code": "UNSUPPORTED_APP", "message": self.message}}
            self.desired = desired
            result = call("config.set", {"patch": desired, "expected_revision": current["revision"]}, "保存模拟设备配置")
            timed_out = not result["ok"] and result.get("error", {}).get("code") == "RESPONSE_TIMEOUT"
            if not result["ok"] and not timed_out:
                self.refresh()
                return result
            self.refresh()
            result = self._verify(desired, source, hashlib.sha256((request_id + "verify").encode()).hexdigest()[:32])
            self.steps.append({"label": "回读核验" + ("（回执超时后确认）" if timed_out else ""),
                               "status": "done" if result["ok"] else "error"})
            if timed_out and result["ok"]:
                self.steps[-2]["status"] = "reconciled"
                result["result"]["timeout_reconciled"] = True
            self.setups[request_id] = (fingerprint, copy.deepcopy(result))
            while len(self.setups) > 128:
                self.setups.popitem(last=False)
            return result
