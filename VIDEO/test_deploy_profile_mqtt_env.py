import json
import os
import shutil
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


# deploy_profile.sh 按形态写进 .env.docker、不允许 compose 的 environment 再兜底覆盖的键
PROFILE_ONLY_KEYS = ("POST_ENABLED", "POST_INGRESS_TRANSPORT", "POST_FAIL_STRATEGY", "POST_FAILOVER_OPEN")
_COMPOSE_PROJECT = "easyaiot-compose-precedence-probe"


def _compose_version_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "compose", "version"], text=True, capture_output=True, check=False
        )
    except OSError:
        return False
    return result.returncode == 0


def _hardcoded_env_entries(compose_text: str, keys: tuple[str, ...]) -> list[str]:
    """compose 文件 environment 列表里写死的指定键（KEY=... 形式的条目）。"""
    return [
        line.strip() for line in compose_text.splitlines()
        if line.lstrip().startswith("- ") and line.strip()[2:].split("=", 1)[0].strip() in keys
    ]


def _render_video_container_env(video_dir: Path, *compose_files: str) -> dict:
    """在临时目录渲染 compose，返回 video-service 最终生效的 environment。"""
    rendered = subprocess.run(
        [
            "docker", "compose", "--project-name", _COMPOSE_PROJECT,
            *[arg for name in compose_files for arg in ("-f", name)],
            "config", "--format", "json",
        ],
        cwd=video_dir,
        # 只带 PATH/HOME：shell 里导出的同名变量会参与 ${VAR:-default} 替换，掩盖被测的覆盖问题
        env={"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", "")},
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(rendered.stdout)["services"]["video-service"]["environment"]


class TestDeployProfileComposePrecedence(unittest.TestCase):
    """compose 的 environment 会盖过 env_file：脚本写进 .env.docker 的值必须原样进容器。"""

    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tempdir.cleanup)
        self.root = Path(self._tempdir.name)
        self.video_dir = self.root / "VIDEO"
        self.video_dir.mkdir()
        shutil.copyfile(REPO_ROOT / "VIDEO" / "docker-compose.yaml", self.video_dir / "docker-compose.yaml")

    def _rendered_env(self, *, profile: str, desktop_os: str | None) -> dict:
        _seed_env(self.root)
        _apply_profile(self.root, profile=profile, desktop_os=desktop_os)
        return _render_video_container_env(self.video_dir, "docker-compose.yaml")

    def test_compose_does_not_hardcode_profile_only_keys(self) -> None:
        for name, keys in (
            ("docker-compose.yaml", PROFILE_ONLY_KEYS),
            ("docker-compose.desktop.yaml", ("ALGO_BUS_TRANSPORT",)),
        ):
            with self.subTest(compose_file=name):
                text = (REPO_ROOT / "VIDEO" / name).read_text(encoding="utf-8")
                self.assertEqual(_hardcoded_env_entries(text, keys), [])

    @unittest.skipUnless(_compose_version_available(), "需要 docker compose 才能渲染")
    def test_post_switch_written_by_deploy_profile_reaches_the_container(self) -> None:
        for profile, expected in (("edge", "false"), ("mini", "false"), ("standard", "true"), ("full", "true")):
            with self.subTest(profile=profile):
                container_env = self._rendered_env(profile=profile, desktop_os=None)
                self.assertEqual(container_env.get("POST_ENABLED"), expected)
        self.assertEqual(self._rendered_env(profile="edge", desktop_os=None).get("ALGO_BUS_TRANSPORT"), "http")

    @unittest.skipUnless(_compose_version_available(), "需要 docker compose 才能渲染")
    def test_desktop_override_no_longer_forces_edge_back_onto_mqtt(self) -> None:
        shutil.copyfile(
            REPO_ROOT / "VIDEO" / "docker-compose.desktop.yaml", self.video_dir / "docker-compose.desktop.yaml"
        )
        for profile, expected in (("edge", "http"), ("mini", "mqtt")):
            with self.subTest(profile=profile):
                _seed_env(self.root)
                _apply_profile(self.root, profile=profile, desktop_os="mac")
                container_env = _render_video_container_env(
                    self.video_dir, "docker-compose.yaml", "docker-compose.desktop.yaml"
                )
                self.assertEqual(container_env.get("ALGO_BUS_TRANSPORT"), expected)
                self.assertEqual(container_env.get("MQTT_BROKER_URLS"), "emqx-server:1883")


if __name__ == "__main__":
    unittest.main()
