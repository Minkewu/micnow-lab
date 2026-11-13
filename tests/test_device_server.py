"""Agent CLI and Web share one real local service; neither edits state files."""
import http.client
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "micnow-lab" / "scripts"


class DeviceServerTest(unittest.TestCase):
    def setUp(self):
        self.process = subprocess.Popen([sys.executable, str(SCRIPTS / "serve_device_lab.py"), "--port", "0"],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.cleanup)
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(5), "service did not start")
            line = self.process.stdout.readline()
        self.assertTrue(line, self.process.stderr.read() if self.process.poll() is not None else "no startup line")
        self.startup = json.loads(line)
        self.port = self.startup["port"]
        _, initial = self.request("GET", "/api/state")
        self.token = initial["token"]

    def cleanup(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)
        self.process.stdout.close()
        self.process.stderr.close()

    def request(self, method, path, data=None, headers=None, raw=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        prepared = {"Content-Type": "application/json"}
        if hasattr(self, "token"):
            prepared["X-MicNow-Token"] = self.token
        prepared.update(headers or {})
        try:
            connection.request(method, path, body=raw if raw is not None else json.dumps(data) if data is not None else None,
                               headers=prepared)
            response = connection.getresponse()
            self.assertIsNone(response.getheader("Access-Control-Allow-Origin"))
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def client(self, *arguments):
        result = subprocess.run([sys.executable, str(SCRIPTS / "device_client.py"), "--connection",
                                 self.startup["connection_file"], *arguments], capture_output=True, text=True)
        self.assertNotIn(self.token, result.stdout + result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_cli_and_web_operate_same_simulated_device(self):
        _, before = self.request("GET", "/api/state")
        code, result = self.client("setup", "--shortcut", "LeftOption", "--speak-mode", "toggle", "--id", "agent-setup")
        self.assertEqual(code, 0, result)
        _, after = self.request("GET", "/api/state")
        self.assertEqual(after["state"]["session_id"], before["state"]["session_id"])
        self.assertEqual(after["state"]["config"]["shortcut"], "LeftOption")
        self.assertTrue(after["state"]["verification"]["config"])
        self.assertTrue(all(c["source"] == "agent" for c in after["state"]["commands"]))
        self.request("POST", "/api/setup", {"shortcut": "RightOption", "source": "web"})
        _, current = self.client("state")
        self.assertEqual(current["state"]["config"]["shortcut"], "RightOption")
        self.assertEqual(current["state"]["commands"][-1]["source"], "web")

    def test_private_connection_file_and_no_token_in_startup_or_cli(self):
        self.assertNotIn("token", self.startup)
        mode = stat.S_IMODE(Path(self.startup["connection_file"]).stat().st_mode)
        self.assertEqual(mode, 0o600)
        _, data = self.client("state")
        self.assertNotIn("token", data)

    def test_host_origin_and_mutation_token_are_enforced(self):
        for headers in [{"Host": "attacker.example"}, {"Origin": "https://attacker.example"},
                        {"Sec-Fetch-Site": "cross-site"}]:
            status, _ = self.request("GET", "/api/state", headers=headers)
            self.assertEqual(status, 403)
        status, _ = self.request("POST", "/api/setup", {}, {"X-MicNow-Token": "wrong"})
        self.assertEqual(status, 403)

    def test_malformed_command_preserves_configuration(self):
        _, before = self.request("GET", "/api/state")
        status, result = self.request("POST", "/api/command", {"command": "config.set", "args": [], "source": "agent"})
        self.assertEqual(status, 400)
        self.assertFalse(result["ok"])
        status, result = self.request("POST", "/api/command", {"command": "config.set", "args": {"patch": {"unknown": 1}, "expected_revision": 0}})
        self.assertFalse(result["ok"])
        _, after = self.request("GET", "/api/state")
        self.assertEqual(before["state"]["config"], after["state"]["config"])

    def test_reset_creates_new_device_session_and_clears_trace(self):
        _, before = self.client("setup", "--shortcut", "LeftOption")
        status, reset = self.request("POST", "/api/reset", {"source": "web"})
        self.assertEqual(status, 200)
        self.assertNotEqual(before["state"]["session_id"], reset["state"]["session_id"])
        self.assertEqual(reset["state"]["commands"], [])
        self.assertFalse(reset["state"]["verification"]["config"])

    def test_shutdown_cleans_connection_file(self):
        code, result = self.client("shutdown")
        self.assertEqual(code, 0, result)
        self.process.wait(timeout=4)
        self.assertFalse(Path(self.startup["connection_file"]).exists())


if __name__ == "__main__":
    unittest.main()
