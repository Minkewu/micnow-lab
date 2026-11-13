#!/usr/bin/env python3
"""A bounded JSONL MicNow simulator process. Never touches real hardware or apps."""
import copy
import json
import sys
import time
import uuid
from collections import OrderedDict

PROTOCOL = "micnow-lab/0.4"
MAX_FRAME = 16384
SCENARIOS = ("ready", "disconnected", "receiver-only", "permission-required",
             "write-timeout", "readback-mismatch", "audio-silent", "unsupported-app")
CAPABILITIES = ["device.info", "device.capabilities", "device.status", "config.get",
                "config.set", "speak.press", "speak.release", "speak.test"]


class DeviceError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def require(test, code, message):
    if not test:
        raise DeviceError(code, message)


def valid_shortcut(value):
    return (isinstance(value, str) and 0 < len(value) <= 64
            and value == value.strip() and all(ord(c) >= 32 for c in value))


class Device:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.config = {"shortcut": "RightOption", "speak_mode": "hold",
                       "target_app": "codex", "voice_tool": "typeless"}
        self.revision = 0
        self.write_count = 0
        self.sequence = 0
        self.receiver = self.microphone = True
        self.permission = "granted-fixture"
        self.scenario = "ready"
        self.armed = False
        self.pressed = self.active = False
        self.events = []
        self.requests = OrderedDict()

    def event(self, kind, message):
        self.sequence += 1
        self.events.append({"id": self.sequence, "at": time.time(), "type": kind, "message": message})
        self.events = self.events[-80:]

    def available(self):
        require(self.receiver and self.microphone, "DEVICE_DISCONNECTED", "模拟麦克风尚未连接。")
        require(self.permission != "required", "PERMISSION_REQUIRED", "请先完成模拟授权。")

    def snapshot(self):
        return {"session_id": self.session_id, "sequence": self.sequence,
                "simulation": True, "real_hardware_connected": False,
                "audio_captured": False, "external_apps_modified": False,
                "protocol_status": "draft-not-firmware", "protocol_version": PROTOCOL,
                "device": {"id": "SIM-MICNOW-" + self.session_id[:8], "name": "MicNow",
                           "firmware_version": "sim-0.4", "capabilities": CAPABILITIES},
                "connection": {"connected": self.receiver and self.microphone,
                               "receiver": self.receiver, "microphone": self.microphone,
                               "permission": self.permission},
                "config": dict(self.config), "revision": self.revision,
                "write_count": self.write_count, "scenario": self.scenario,
                "speak": {"pressed": self.pressed, "active": self.active,
                          "light": "off" if not self.microphone else "listening" if self.active else "ready"},
                "events": copy.deepcopy(self.events)}

    def execute(self, command, args):
        require(isinstance(args, dict), "INVALID_ARGUMENT", "args 必须是对象。")
        empty = {"device.info", "device.capabilities", "device.status", "config.get",
                 "speak.press", "speak.release", "speak.test", "lab.snapshot"}
        if command in empty:
            require(not args, "INVALID_ARGUMENT", "此命令不接受参数。")
        if command == "lab.snapshot":
            return self.snapshot()
        if command == "lab.scenario":
            require(set(args) == {"name"} and args["name"] in SCENARIOS,
                    "INVALID_ARGUMENT", "未知的模拟场景。")
            self.scenario = args["name"]
            self.armed = self.scenario == "write-timeout"
            self.receiver = self.scenario != "disconnected"
            self.microphone = self.scenario not in ("disconnected", "receiver-only")
            if self.scenario == "permission-required":
                self.permission = "required"
            self.pressed = self.active = False
            self.event("scenario.changed", "模拟场景已切换：" + self.scenario)
            return {"scenario": self.scenario}
        if command == "lab.permission":
            require(set(args) == {"allow"} and args["allow"] is True,
                    "INVALID_ARGUMENT", "仅接受明确的模拟允许。")
            self.permission = "allowed-simulated"
            self.event("permission.allowed", "已允许本次模拟连接；未改变系统权限。")
            return {"permission": self.permission}
        if command not in CAPABILITIES:
            raise DeviceError("UNKNOWN_COMMAND", "模拟设备不支持此命令。")
        self.available()
        if command == "device.info":
            return self.snapshot()["device"]
        if command == "device.capabilities":
            return {"commands": CAPABILITIES, "config_fields": list(self.config),
                    "device_candidate_fields": ["shortcut", "speak_mode"],
                    "host_profile_fields": ["target_app", "voice_tool"],
                    "host_profile_note": "主机意图仅随模拟配置存储，不是固件要求或真实应用配置。",
                    "supported_apps": ["codex", "general"] if self.scenario == "unsupported-app"
                    else ["codex", "workbuddy", "general"]}
        if command == "device.status":
            return {"connected": True, "permission": self.permission,
                    "revision": self.revision, "speak": self.snapshot()["speak"]}
        if command == "config.get":
            return {"config": dict(self.config), "revision": self.revision}
        if command == "config.set":
            require(set(args) == {"patch", "expected_revision"}, "INVALID_ARGUMENT",
                    "写入需提供 patch 和 expected_revision。")
            patch = args["patch"]
            require(isinstance(patch, dict) and bool(patch) and set(patch) <= set(self.config),
                    "INVALID_ARGUMENT", "配置字段无效。")
            require(type(args["expected_revision"]) is int and args["expected_revision"] == self.revision,
                    "REVISION_CONFLICT", "配置已变化，请重新读取后决定。")
            require("shortcut" not in patch or valid_shortcut(patch["shortcut"]),
                    "INVALID_ARGUMENT", "快捷键格式无效。")
            require("speak_mode" not in patch or patch["speak_mode"] in ("hold", "toggle"),
                    "INVALID_ARGUMENT", "Speak 模式无效。")
            require("target_app" not in patch or patch["target_app"] in ("codex", "workbuddy", "general"),
                    "INVALID_ARGUMENT", "目标应用无效。")
            require("voice_tool" not in patch or patch["voice_tool"] == "typeless",
                    "INVALID_ARGUMENT", "本版仅提供 Typeless 配置样例。")
            desired = dict(self.config, **patch)
            require(not (self.scenario == "unsupported-app" and desired["target_app"] == "workbuddy"),
                    "UNSUPPORTED_APP", "此模拟场景未支持 WorkBuddy。")
            changed = desired != self.config or self.scenario == "readback-mismatch"
            if changed:
                if self.scenario == "readback-mismatch":
                    desired["speak_mode"] = "toggle" if desired["speak_mode"] == "hold" else "hold"
                self.config = desired
                self.revision += 1
                self.write_count += 1
                self.pressed = self.active = False
                self.event("config.saved", "模拟设备已保存配置 v" + str(self.revision))
            return {"accepted": True, "changed": changed, "revision": self.revision}
        if command == "speak.press":
            if not self.pressed:
                self.pressed = True
                self.active = not self.active if self.config["speak_mode"] == "toggle" else True
                self.event("speak.pressed", "模拟 Speak 已按下。")
            return self.snapshot()["speak"]
        if command == "speak.release":
            if self.pressed:
                self.pressed = False
                if self.config["speak_mode"] == "hold":
                    self.active = False
                self.event("speak.released", "模拟 Speak 已松开。")
            return self.snapshot()["speak"]
        if command == "speak.test":
            require(self.scenario != "audio-silent", "SIMULATED_AUDIO_SILENT", "本次模拟试说没有声音，请检查后重试。")
            self.event("speak.fixture", "预置试说样例返回；未录音或识别真实语音。")
            return {"text": "把今天讨论的想法整理成下一步行动。", "source": "canned-fixture",
                    "audio_captured": False, "target_app": self.config["target_app"]}

    def handle(self, request):
        request_id = request.get("id") if isinstance(request, dict) else None
        try:
            require(isinstance(request, dict) and set(request) == {"protocol", "id", "command", "args"},
                    "INVALID_FRAME", "消息结构无效。")
            require(request["protocol"] == PROTOCOL, "PROTOCOL_MISMATCH", "模拟协议版本不匹配。")
            require(isinstance(request_id, str) and 0 < len(request_id) <= 96,
                    "INVALID_ID", "请求 ID 无效。")
            require(isinstance(request["command"], str), "INVALID_COMMAND", "命令名无效。")
            fingerprint = json.dumps([request["command"], request["args"]], sort_keys=True)
            if request_id in self.requests:
                old_fingerprint, response = self.requests[request_id]
                require(old_fingerprint == fingerprint, "ID_CONFLICT", "同一请求 ID 不能用于不同指令。")
                return copy.deepcopy(response), False
            result = self.execute(request["command"], request["args"])
            response = {"protocol": PROTOCOL, "id": request_id, "ok": True,
                        "result": result, "revision": self.revision, "simulation": True}
            drop = request["command"] == "config.set" and self.armed
            if drop:
                self.armed = False
                self.event("ack.lost", "模拟保存已完成，但本次回执丢失。")
            self.requests[request_id] = (fingerprint, copy.deepcopy(response))
            while len(self.requests) > 256:
                self.requests.popitem(last=False)
            return response, drop
        except DeviceError as error:
            return {"protocol": PROTOCOL, "id": request_id, "ok": False,
                    "error": {"code": error.code, "message": error.message},
                    "revision": self.revision, "simulation": True}, False


def main():
    device = Device()
    for raw in iter(lambda: sys.stdin.buffer.readline(MAX_FRAME + 1), b""):
        if len(raw) > MAX_FRAME or not raw.endswith(b"\n"):
            break
        try:
            request = json.loads(raw)
        except (ValueError, UnicodeError):
            request = None
        response, drop = device.handle(request)
        if not drop:
            sys.stdout.buffer.write(json.dumps(response, ensure_ascii=False).encode() + b"\n")
            sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
