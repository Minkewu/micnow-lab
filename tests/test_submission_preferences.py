"""Regression checks for initial preferences versus later user changes.

Exercises the distributed Skill through its actual simulator subprocess.
"""
from pathlib import Path
import sys
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "micnow-lab" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from device_bridge import Bridge


class SubmissionPreferenceTest(unittest.TestCase):
    def bridge(self, known_shortcut):
        bridge = Bridge(known_shortcut)
        self.addCleanup(bridge.close)
        return bridge

    def setup_ok(self, bridge, data, source="agent"):
        result = bridge.setup(data, source)
        self.assertTrue(result["ok"], result)
        state = bridge.state()
        self.assertTrue(state["verification"]["config"], state)
        return state

    def set_shortcut(self, bridge, shortcut):
        revision = bridge.state()["revision"]
        result = bridge.command("config.set", {"patch": {"shortcut": shortcut},
                                                "expected_revision": revision}, "web")
        self.assertTrue(result["ok"], result)
        return bridge.state()

    def test_initial_known_shortcut_is_applied(self):
        bridge = self.bridge("LeftOption")
        state = self.setup_ok(bridge, {})
        self.assertEqual(state["config"]["shortcut"], "LeftOption")
        self.assertEqual(state["write_count"], 1)

    def test_later_web_setup_preference_survives_ai_mode_change(self):
        bridge = self.bridge("RightOption")
        self.setup_ok(bridge, {})
        self.setup_ok(bridge, {"shortcut": "LeftOption"}, "web")
        state = self.setup_ok(bridge, {"speak_mode": "toggle"})
        self.assertEqual(state["config"]["shortcut"], "LeftOption")
        self.assertEqual(state["config"]["speak_mode"], "toggle")
        self.assertEqual(state["write_count"], 2)

    def test_direct_web_write_survives_first_ai_setup(self):
        bridge = self.bridge("RightOption")
        self.set_shortcut(bridge, "LeftOption")
        state = self.setup_ok(bridge, {"speak_mode": "toggle"})
        self.assertEqual(state["config"]["shortcut"], "LeftOption")

    def test_recovery_rechecks_current_shortcut_without_rewriting_it(self):
        bridge = self.bridge("RightOption")
        self.setup_ok(bridge, {})
        before = self.set_shortcut(bridge, "LeftOption")
        for scenario in ("disconnected", "ready"):
            result = bridge.command("lab.scenario", {"name": scenario}, "web")
            self.assertTrue(result["ok"], result)
        state = self.setup_ok(bridge, {}, "web")
        self.assertEqual(state["config"]["shortcut"], "LeftOption")
        self.assertEqual(state["write_count"], before["write_count"])
        self.assertEqual(state["revision"], before["revision"])

    def test_explicit_noop_direct_write_overrides_startup_hint(self):
        bridge = self.bridge("LeftOption")
        before = self.set_shortcut(bridge, "RightOption")
        self.assertEqual(before["revision"], 0)
        state = self.setup_ok(bridge, {"speak_mode": "toggle"})
        self.assertEqual(state["config"]["shortcut"], "RightOption")

    def test_explicit_noop_setup_overrides_startup_hint(self):
        bridge = self.bridge("LeftOption")
        before = self.setup_ok(bridge, {"shortcut": "RightOption"}, "web")
        self.assertEqual(before["revision"], 0)
        state = self.setup_ok(bridge, {}, "web")
        self.assertEqual(state["config"]["shortcut"], "RightOption")
        self.assertEqual(state["write_count"], 0)

    def test_matching_startup_hint_does_not_create_redundant_writes(self):
        bridge = self.bridge("RightOption")
        self.setup_ok(bridge, {})
        state = self.setup_ok(bridge, {})
        self.assertEqual(state["config"]["shortcut"], "RightOption")
        self.assertEqual(state["revision"], 0)
        self.assertEqual(state["write_count"], 0)


if __name__ == "__main__":
    unittest.main()
