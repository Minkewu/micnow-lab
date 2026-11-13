#!/usr/bin/env python3
"""Invoke the running local MicNow lab; outputs actual replies without credentials."""
import argparse
import http.client
import json
import os
from pathlib import Path
import stat
import sys
from urllib.parse import urlsplit


def read_connection(value):
    path = Path(value).expanduser().absolute()
    info = path.lstat()
    if (path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_size > 4096
            or (hasattr(os, "getuid") and info.st_uid != os.getuid())):
        raise ValueError("连接文件无效或不属于当前用户。")
    connection = json.loads(path.read_text())
    url = urlsplit(connection.get("url", ""))
    if (connection.get("format") != "micnow-lab-connection/0.4" or url.scheme != "http"
            or url.hostname != "127.0.0.1" or not url.port or url.path not in ("", "/")
            or url.username is not None or url.query or url.fragment
            or not isinstance(connection.get("token"), str)):
        raise ValueError("仅允许连接本机 MicNow 模拟服务。")
    return url.port, connection["token"]


def invoke(connection_file, path, data=None):
    port, token = read_connection(connection_file)
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        client.request("GET" if data is None else "POST", path,
                       body=None if data is None else json.dumps(data),
                       headers={"Content-Type": "application/json", "X-MicNow-Token": token})
        response = client.getresponse()
        result = json.loads(response.read())
        result.pop("token", None)
        return result
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection", required=True)
    subs = parser.add_subparsers(dest="operation", required=True)
    subs.add_parser("state", aliases=["status"])
    setup = subs.add_parser("setup")
    setup.add_argument("--shortcut")
    setup.add_argument("--speak-mode", choices=["hold", "toggle"])
    setup.add_argument("--target-app", choices=["codex", "workbuddy", "general"])
    setup.add_argument("--id")
    command = subs.add_parser("command")
    command.add_argument("name")
    command.add_argument("--args", default="{}")
    command.add_argument("--id")
    subs.add_parser("reset")
    subs.add_parser("shutdown")
    args = parser.parse_args()
    try:
        if args.operation in ("state", "status"):
            result = invoke(args.connection, "/api/state")
        elif args.operation == "setup":
            data = {key: getattr(args, key) for key in ("shortcut", "speak_mode", "target_app", "id")
                    if getattr(args, key) is not None}
            result = invoke(args.connection, "/api/setup", dict(data, source="agent"))
        elif args.operation == "command":
            data = {"command": args.name, "args": json.loads(args.args), "source": "agent"}
            if args.id is not None:
                data["id"] = args.id
            result = invoke(args.connection, "/api/command", data)
        else:
            result = invoke(args.connection, "/api/" + args.operation, {"source": "agent"})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1
    except (OSError, ValueError, http.client.HTTPException) as error:
        print(json.dumps({"ok": False, "simulation": True,
                          "error": {"code": "LOCAL_CONNECTION_ERROR", "message": str(error)}}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
