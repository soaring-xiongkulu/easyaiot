#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "standalone_manifest.py"


class StandaloneManifestTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / "a.rknn").write_bytes(b"model-a")
        (self.base / "b.rknn").write_bytes(b"model-b")
        (self.base / "classes.names").write_text("person\ncar\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def run_compile(self, document):
        manifest = self.base / "tasks.json"
        manifest.write_text(json.dumps(document), encoding="utf-8")
        output = self.base / "out"
        result = subprocess.run([
            "python3", str(SCRIPT), "compile",
            "--manifest", str(manifest),
            "--output", str(output),
            "--prefix", "/opt/easyaiot/RUNTIME-RK3588",
            "--log-dir", "/var/log/easyaiot/runtime-rk3588",
            "--default-classes", str(self.base / "classes.names"),
        ], text=True, capture_output=True)
        return result, output

    def document(self):
        return {
            "version": 1,
            "models": {
                "people": {"path": "a.rknn", "classes": "classes.names", "business_model_id": 1},
                "helmet": {"path": "b.rknn", "classes": "classes.names", "business_model_id": 2},
            },
            "tasks": [
                {"id": "gate", "rtsp_url": "rtsp://camera/gate", "models": ["people", "helmet"], "control_port": 8201},
                {"id": "yard", "rtsp_url": "rtsp://camera/yard", "models": ["people"], "control_port": 8202},
            ],
        }

    def test_compiles_one_ini_per_stream_and_multiple_models(self):
        result, output = self.run_compile(self.document())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 路 RTSP、2 个 RKNN 模型、3 个任务模型绑定", result.stdout)
        gate = (output / "tasks" / "gate.ini").read_text(encoding="utf-8")
        self.assertIn("model_path=/opt/easyaiot/RUNTIME-RK3588/models/people.rknn", gate)
        self.assertIn("model_path_helmet=/opt/easyaiot/RUNTIME-RK3588/models/helmet.rknn", gate)
        self.assertTrue((output / "tasks" / "yard.ini").is_file())

    def test_rejects_duplicate_control_ports(self):
        document = self.document()
        document["tasks"][1]["control_port"] = 8201
        result, _ = self.run_compile(document)
        self.assertEqual(result.returncode, 2)
        self.assertIn("控制端口重复", result.stderr)

    def test_rejects_undefined_model(self):
        document = self.document()
        document["tasks"][0]["models"] = ["missing"]
        result, _ = self.run_compile(document)
        self.assertEqual(result.returncode, 2)
        self.assertIn("未定义模型", result.stderr)

    def test_compiles_control_plane_and_optional_frp(self):
        document = self.document()
        document["control_plane"] = {
            "enabled": True,
            "url": "http://platform.example/admin-api/video/edge",
            "join_token": "join-secret",
            "node_name": "rk3588-lab",
            "heartbeat_interval_seconds": 10,
            "agent_port": 9100,
        }
        document["remote_access"] = {
            "enabled": True,
            "provider": "frp",
            "server_addr": "frp.example.com",
            "server_port": 7000,
            "auth_token": "frp-secret",
            "frpc_binary": "/usr/local/bin/frpc",
            "service": {"enabled": True, "remote_port": 19100},
            "ssh": {"enabled": True, "remote_port": 16022, "username": "rock"},
        }
        result, output = self.run_compile(document)
        self.assertEqual(result.returncode, 0, result.stderr)
        agent = json.loads((output / "edge-agent.json").read_text(encoding="utf-8"))
        self.assertTrue(agent["enabled"])
        self.assertEqual(agent["remote_access"]["sshAccessPort"], 16022)
        frpc = (output / "frpc.toml").read_text(encoding="utf-8")
        self.assertIn('name = "easyaiot-edge-service"', frpc)
        self.assertIn('name = "easyaiot-edge-ssh"', frpc)

    def test_rejects_frp_without_control_plane(self):
        document = self.document()
        document["remote_access"] = {
            "enabled": True,
            "server_addr": "frp.example.com",
            "auth_token": "secret",
        }
        result, _ = self.run_compile(document)
        self.assertEqual(result.returncode, 2)
        self.assertIn("必须先启用 control_plane", result.stderr)

    def test_root_installer_forwards_manifest_to_config_check(self):
        manifest = self.base / "tasks.json"
        manifest.write_text(json.dumps(self.document()), encoding="utf-8")
        env = os.environ.copy()
        env.update({
            "EASYAIOT_RK3588_INSTALL_DIR": str(self.base / "install"),
            "EASYAIOT_RK3588_STATE_DIR": str(self.base / "state"),
            "EASYAIOT_RK3588_LOG_DIR": str(self.base / "logs"),
        })
        result = subprocess.run([
            "bash", str(ROOT.parent / ".scripts" / "docker" / "install_linux.sh"),
            "rk3588", "config-check", str(manifest),
        ], cwd=ROOT.parent, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("任务清单可部署", result.stdout)


if __name__ == "__main__":
    unittest.main()
