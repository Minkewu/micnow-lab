"""Meaningful protocol tests use a real subprocess and byte transport, without hardware."""
import json
import os
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "micnow-lab" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from device_bridge import Bridge, BridgeError


class DeviceBridgeTest(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge("RightOption")
        self.addCleanup(self.bridge.close)

    def command(self, name, args=None, request_id=None):
        return self.bridge.command(name, args or {}, "agent", request_id)

    def test_separate_simulator_process_and_transport(self):
        self.assertNotEqual(self.bridge.transport.process.pid, os.getpid())
        state = self.bridge.state()
        self.assertTrue(state["simulation"])
        self.assertFalse(state["verification"]["config"])
        self.assertEqual(state["workflow"]["phase"], "idle")
        self.assertIn(state["connection"]["transport"], ("pty", "pipe"))
        response = self.command("device.info")
        self.assertTrue(response["ok"])
        self.assertTrue(self.bridge.state()["commands"][-1]["transport_io"])

    def test_setup_records_actual_commands_and_readback(self):
        result = self.bridge.setup({"speak_mode": "toggle"}, "agent", "setup-one")
        self.assertTrue(result["ok"], result)
        state = self.bridge.state()
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["verified_revision"], 1)
        self.assertEqual(state["workflow"]["phase"], "waiting-trial")
        self.assertEqual([c["command"] for c in state["commands"]],
                         ["device.info", "device.capabilities", "config.get", "config.set", "config.get"])
        self.assertTrue(all(c["source"] == "agent" for c in state["commands"]))

    def test_idempotency_and_revision_conflict(self):
        args = {"patch": {"shortcut": "LeftOption"}, "expected_revision": 0}
        one = self.command("config.set", args, "write-once")
        two = self.command("config.set", args, "write-once")
        self.assertEqual(one, two)
        self.assertEqual(self.bridge.state()["write_count"], 1)
        changed = self.command("config.set", {"patch": {"shortcut": "RightOption"}, "expected_revision": 1}, "write-once")
        self.assertEqual(changed["error"]["code"], "ID_CONFLICT")
        stale = self.command("config.set", {"patch": {"shortcut": "RightOption"}, "expected_revision": 0})
        self.assertEqual(stale["error"]["code"], "REVISION_CONFLICT")
        self.assertEqual(self.bridge.state()["config"]["shortcut"], "LeftOption")

    def test_timeout_readback_without_duplicate_write(self):
        self.command("lab.scenario", {"name": "write-timeout"})
        result = self.bridge.setup({"speak_mode": "toggle"}, "agent")
        self.assertTrue(result["ok"], result)
        self.assertTrue(result["result"]["timeout_reconciled"])
        state = self.bridge.state()
        self.assertEqual(state["write_count"], 1)
        self.assertTrue(state["verification"]["config"])
        timeouts = [c for c in state["commands"] if c["status"] == "RESPONSE_TIMEOUT"]
        self.assertEqual(len(timeouts), 1)
        self.assertEqual(timeouts[0]["response"]["outcome"], "unknown")

    def test_wrong_readback_stops_and_never_marks_ready(self):
        self.command("lab.scenario", {"name": "readback-mismatch"})
        result = self.bridge.setup({"shortcut": "LeftOption", "speak_mode": "toggle"}, "agent")
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "READBACK_MISMATCH")
        state = self.bridge.state()
        self.assertEqual(state["write_count"], 1)
        self.assertFalse(state["verification"]["config"])
        self.assertEqual(state["workflow"]["phase"], "blocked-readback")

    def test_disconnect_invalidates_readiness_reconnect_retains_configuration(self):
        self.bridge.setup({"shortcut": "LeftOption"}, "agent")
        self.assertTrue(self.command("speak.test")["ok"])
        self.command("lab.scenario", {"name": "disconnected"})
        offline = self.bridge.state()
        self.assertFalse(offline["verification"]["trial"])
        self.assertEqual(offline["workflow"]["phase"], "waiting-connection")
        self.assertEqual(self.command("config.get")["error"]["code"], "DEVICE_DISCONNECTED")
        self.command("lab.scenario", {"name": "ready"})
        self.assertEqual(self.bridge.state()["config"]["shortcut"], "LeftOption")
        self.assertFalse(self.bridge.state()["verification"]["config"])

    def test_permission_cannot_be_fixed_by_restoring_scenario(self):
        self.command("lab.scenario", {"name": "permission-required"})
        blocked = self.bridge.setup({}, "agent")
        self.assertEqual(blocked["error"]["code"], "PERMISSION_REQUIRED")
        self.command("lab.scenario", {"name": "ready"})
        self.assertEqual(self.bridge.state()["workflow"]["phase"], "waiting-permission")
        self.command("lab.permission", {"allow": True})
        self.assertTrue(self.bridge.setup({}, "agent")["ok"])

    def test_speak_modes_and_fixture_are_explicit(self):
        self.bridge.setup({"speak_mode": "hold"}, "agent")
        self.command("speak.press")
        self.assertTrue(self.bridge.state()["speak"]["active"])
        self.command("speak.release")
        self.assertFalse(self.bridge.state()["speak"]["active"])
        trial = self.command("speak.test")
        self.assertEqual(trial["result"]["source"], "canned-fixture")
        self.assertFalse(trial["result"]["audio_captured"])
        self.bridge.setup({"speak_mode": "toggle"}, "agent")
        self.command("speak.press")
        self.command("speak.release")
        self.assertTrue(self.bridge.state()["speak"]["active"])
        self.command("speak.press")
        self.command("speak.release")
        self.assertFalse(self.bridge.state()["speak"]["active"])

    def test_silent_trial_and_unsupported_app_never_fake_success(self):
        self.command("lab.scenario", {"name": "audio-silent"})
        self.bridge.setup({}, "agent")
        self.assertFalse(self.command("speak.test")["ok"])
        self.assertEqual(self.bridge.state()["workflow"]["phase"], "waiting-audio")
        self.command("lab.scenario", {"name": "unsupported-app"})
        result = self.bridge.setup({"target_app": "workbuddy"}, "agent")
        self.assertEqual(result["error"]["code"], "UNSUPPORTED_APP")
        self.assertFalse(self.bridge.state()["verification"]["config"])

    def test_dead_device_clears_stale_success(self):
        self.bridge.setup({}, "agent")
        self.bridge.transport.process.terminate()
        self.bridge.transport.process.wait(timeout=2)
        state = self.bridge.state()
        self.assertFalse(state["connection"]["connected"])
        self.assertFalse(state["verification"]["config"])

    def test_cached_setup_cannot_claim_current_success_after_other_write(self):
        self.bridge.setup({"shortcut": "LeftOption"}, "agent", "old-setup")
        self.bridge.setup({"shortcut": "RightOption"}, "web", "new-setup")
        old = self.bridge.setup({"shortcut": "LeftOption"}, "agent", "old-setup")
        # A historical successful receipt must not replace the newer desired configuration.
        self.assertFalse(old["ok"])
        self.assertEqual(old["error"]["code"], "STALE_OPERATION")
        self.assertEqual(self.bridge.state()["config"]["shortcut"], "RightOption")


if __name__ == "__main__":
    unittest.main()
