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


def _seed_env(root: Path) -> None:
    for module in ("AI", "VIDEO"):
        module_dir = root / module
        module_dir.mkdir(parents=True, exist_ok=True)
        (module_dir / ".env").write_text("", encoding="utf-8")
        (module_dir / ".env.docker").write_text(
            "ALGO_BUS_TRANSPORT=http\n"
            "MQTT_BROKER_URLS=127.0.0.1:1883\n",
            encoding="utf-8",
        )


def _apply_profile(root: Path, *, profile: str, desktop_os: str | None) -> None:
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
            str(root),
        ],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )


class TestDeployProfileMqttEnv(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_non_edge_desktop_profiles_use_emqx_service(self) -> None:
        for profile in ("mini", "standard", "full"):
            with self.subTest(profile=profile):
                _seed_env(self.root)
                _apply_profile(self.root, profile=profile, desktop_os="mac")

                values = _read_env(self.root / "VIDEO" / ".env.docker")
                self.assertEqual(values["ALGO_BUS_TRANSPORT"], "mqtt")
                self.assertEqual(values["MQTT_BROKER_URLS"], "emqx-server:1883")

    def test_non_edge_linux_uses_host_network_broker(self) -> None:
        _seed_env(self.root)
        _apply_profile(self.root, profile="mini", desktop_os=None)

        values = _read_env(self.root / "VIDEO" / ".env.docker")
        self.assertEqual(values["ALGO_BUS_TRANSPORT"], "mqtt")
        self.assertEqual(values["MQTT_BROKER_URLS"], "127.0.0.1:1883")

    def test_switching_from_edge_to_mini_clears_stale_bus_config(self) -> None:
        _seed_env(self.root)
        _apply_profile(self.root, profile="edge", desktop_os="mac")

        edge_values = _read_env(self.root / "VIDEO" / ".env.docker")
        self.assertEqual(edge_values["ALGO_BUS_TRANSPORT"], "http")

        _apply_profile(self.root, profile="mini", desktop_os="mac")

        mini_values = _read_env(self.root / "VIDEO" / ".env.docker")
        self.assertEqual(mini_values["ALGO_BUS_TRANSPORT"], "mqtt")
        self.assertEqual(mini_values["MQTT_BROKER_URLS"], "emqx-server:1883")


if __name__ == "__main__":
    unittest.main()
