import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_PROFILE_SCRIPT = REPO_ROOT / ".scripts" / "docker" / "deploy_profile.sh"


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def _apply_profile(tmp_path: Path, *, profile: str, desktop_os: str | None) -> None:
    for module in ("AI", "VIDEO"):
        module_dir = tmp_path / module
        module_dir.mkdir(parents=True)
        (module_dir / ".env").write_text(
            "MINIO_ENABLED=false\nMINIO_ENDPOINT=localhost:9000\n",
            encoding="utf-8",
        )
        (module_dir / ".env.docker").write_text(
            "MINIO_ENABLED=false\nMINIO_ENDPOINT=localhost:9000\n",
            encoding="utf-8",
        )

    env = os.environ.copy()
    env["EASYAIOT_DEPLOY_PROFILE"] = profile
    env.pop("EASYAIOT_DESKTOP_OS", None)
    env.pop("EASYAIOT_COMPOSE_DESKTOP", None)
    if desktop_os:
        env["EASYAIOT_DESKTOP_OS"] = desktop_os

    subprocess.run(
        [
            "bash",
            "-c",
            # Media-path generation is independent from this contract and may
            # inspect host mounts, so isolate it in this focused env test.
            'source "$1"; _apply_python_sink_media_env() { :; }; '
            'apply_python_service_deploy_env "$2"',
            "deploy-profile-test",
            str(DEPLOY_PROFILE_SCRIPT),
            str(tmp_path),
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )


class TestDeployProfileMinioEnv(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_mini_desktop_ai_uses_shared_minio(self) -> None:
        _apply_profile(self.root, profile="mini", desktop_os="mac")

        for name in (".env", ".env.docker"):
            values = _read_env(self.root / "AI" / name)
            self.assertEqual(values["MINIO_ENABLED"], "true")
            self.assertEqual(
                values["MINIO_ENDPOINT"],
                "host.docker.internal:9000",
            )
            self.assertEqual(values["MODEL_AI_SRS_HOST"], "srs-server")
            self.assertEqual(values["MODEL_AI_SRS_PLAY_HOST"], "127.0.0.1")

    def test_mini_linux_ai_uses_host_network_minio(self) -> None:
        _apply_profile(self.root, profile="mini", desktop_os=None)

        for name in (".env", ".env.docker"):
            values = _read_env(self.root / "AI" / name)
            self.assertEqual(values["MINIO_ENABLED"], "true")
            self.assertEqual(values["MINIO_ENDPOINT"], "localhost:9000")
            self.assertEqual(values["MODEL_AI_SRS_HOST"], "127.0.0.1")

    def test_edge_does_not_enable_ai_minio(self) -> None:
        _apply_profile(self.root, profile="edge", desktop_os="mac")

        for name in (".env", ".env.docker"):
            values = _read_env(self.root / "AI" / name)
            self.assertEqual(values["MINIO_ENABLED"], "false")
            self.assertEqual(values["MINIO_ENDPOINT"], "localhost:9000")


if __name__ == "__main__":
    unittest.main()
