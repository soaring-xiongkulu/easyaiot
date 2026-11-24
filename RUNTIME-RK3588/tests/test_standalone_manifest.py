#!/usr/bin/env python3
import json
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


if __name__ == "__main__":
    unittest.main()
