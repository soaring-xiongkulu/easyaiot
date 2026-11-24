#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("edge_agent", ROOT / "scripts" / "edge_agent.py")
edge_agent = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(edge_agent)


class EdgeAgentTest(unittest.TestCase):
    def test_signed_envelope_round_trip(self):
        envelope = edge_agent.sign_envelope("secret", "command", 7, {
            "commandId": "cmd-1", "command": "status", "params": {},
        })
        payload = edge_agent.verify_envelope(envelope, "secret", 7, "command")
        self.assertEqual(payload["command"], "status")

    def test_signature_rejects_payload_tampering(self):
        envelope = edge_agent.sign_envelope("secret", "command", 7, {"command": "status"})
        envelope["payload"] = json.dumps({"command": "runtime.restart"})
        with self.assertRaisesRegex(ValueError, "签名无效"):
            edge_agent.verify_envelope(envelope, "secret", 7, "command")

    def test_task_rows_use_installed_sibling_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "edge-agent.json"
            config.write_text(json.dumps({"enabled": True}), encoding="utf-8")
            (root / "tasks.tsv").write_text("north\t8201\nwarehouse\t8202\n", encoding="utf-8")
            agent = edge_agent.Agent(config)
            self.assertEqual(agent.task_rows(), [("north", 8201), ("warehouse", 8202)])


if __name__ == "__main__":
    unittest.main()
