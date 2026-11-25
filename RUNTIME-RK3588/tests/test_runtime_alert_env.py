#!/usr/bin/env python3
"""板端原生运行时的 POST 开关。

RUNTIME 未设置 POST_ENABLED 时按 true 处理；板端没有 POST 服务，探活失败后 closed 策略会抑制全部告警。
安装器只有两条启动路径（systemd 模板实例、无 systemd 时的 nohup），两条都必须带上 POST_ENABLED=false。
"""
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install_linux.sh"
TASK_ID = "gate"
UNIT_NAME = "easyaiot-runtime-rk3588@.service"

# 只把被测函数从安装器里取出来执行：整个脚本不能 source，不带参数执行等于 install。
FUNCTIONS = ("install_systemd_template", "service_start", "instance_name", "pid_file", "task_log_file")

HARNESS = r"""set -euo pipefail
{functions}

as_root() {{ "$@"; }}
fail() {{ echo "FAIL: $*" >&2; exit 1; }}
ok() {{ :; }}
warn() {{ :; }}
preflight_runtime() {{ :; }}
require_task_state() {{ :; }}
validate_target_task() {{ :; }}
fallback_running() {{ return 1; }}
selected_task_rows() {{ printf '{task}\t8201\n'; }}
systemd_running() {{ {systemd_running}; }}

PREFIX="$WORK/install"
STATE_DIR="$WORK/state"
TASK_CONFIG_DIR="$STATE_DIR/tasks"
UNIT_FILE="$WORK/systemd/{unit}"
BIN="$WORK/bin/RUNTIME"
RUN_DIR="$PREFIX/run"
LOG_DIR="$WORK/logs"
TMP_DIR="$WORK/tmp"
SERVICE_BASENAME=easyaiot-runtime-rk3588
mkdir -p "$TASK_CONFIG_DIR" "$(dirname "$UNIT_FILE")" "$TMP_DIR"
printf '[video]\n' > "$TASK_CONFIG_DIR/{task}.ini"
{body}
"""

# 真实 RUNTIME 的启动参数是任务 INI；替身只把它拿到的环境变量写到 INI 旁边
FAKE_RUNTIME = """#!/usr/bin/env bash
env > "$1.env"
"""

FAKE_SYSTEMCTL = """#!/usr/bin/env bash
echo "$*" >> "$WORK/systemctl.log"
"""


def installer_functions():
    lines = INSTALLER.read_text(encoding="utf-8").splitlines()
    chunks = []
    for name in FUNCTIONS:
        opener = f"{name}() {{"
        start = next((index for index, line in enumerate(lines) if line.startswith(opener)), None)
        if start is None:
            raise AssertionError(f"安装器里找不到函数 {name}()")
        if lines[start] != opener:
            chunks.append(lines[start])
            continue
        end = next((index for index in range(start + 1, len(lines)) if lines[index] == "}"), None)
        if end is None:
            raise AssertionError(f"安装器函数 {name} 没有顶格的结束大括号")
        chunks.append("\n".join(lines[start:end + 1]))
    return "\n\n".join(chunks)


def unit_sections(text):
    """解析 systemd 单元：节名 → {指令: 值}，注释行不计入。"""
    sections = {"": {}}
    current = sections[""]
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = sections.setdefault(line[1:-1], {})
        elif "=" in line:
            key, value = line.split("=", 1)
            current[key.strip()] = value.strip()
    return sections


class RuntimePostSwitchTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        bin_dir = self.work / "bin"
        bin_dir.mkdir()
        self.write_script(bin_dir / "RUNTIME", FAKE_RUNTIME)
        # 无论测试机有没有 systemd，安装器都只会调到这个替身
        self.write_script(bin_dir / "systemctl", FAKE_SYSTEMCTL)
        self.path = f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"

    @staticmethod
    def write_script(path, content):
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def run_installer_functions(self, body, *, systemd_running=False, post_enabled=None):
        script = HARNESS.format(
            functions=installer_functions(),
            systemd_running="return 0" if systemd_running else "return 1",
            task=TASK_ID,
            unit=UNIT_NAME,
            body=body,
        )
        # 不继承调用方的环境：开发机 shell 里的 POST_ENABLED 不应影响“缺省值”的断言
        env = {"PATH": self.path, "WORK": str(self.work), "HOME": os.environ.get("HOME", "")}
        if post_enabled is not None:
            env["POST_ENABLED"] = post_enabled
        subprocess.run(["bash", "-c", script], env=env, cwd=self.work, text=True, capture_output=True, check=True)

    def post_enabled_seen_by_runtime(self):
        dump = self.work / "state" / "tasks" / f"{TASK_ID}.ini.env"
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if dump.exists():
                found = [line for line in dump.read_text(encoding="utf-8").splitlines()
                         if line.startswith("POST_ENABLED=")]
                if found:
                    return found[0].split("=", 1)[1]
            time.sleep(0.05)
        seen = dump.read_text(encoding="utf-8") if dump.exists() else "(进程未启动)"
        self.fail(f"回退启动的 RUNTIME 没有拿到 POST_ENABLED：\n{seen}")

    def test_systemd_unit_starts_the_runtime_with_post_disabled(self):
        self.run_installer_functions("install_systemd_template")

        sections = unit_sections((self.work / "systemd" / UNIT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(sections["Service"].get("Environment"), "POST_ENABLED=false")
        self.assertEqual(sections["Service"]["ExecStart"], f"{self.work}/bin/RUNTIME {self.work}/state/tasks/%i.ini")

    def test_fallback_launch_without_systemd_disables_post(self):
        self.run_installer_functions('service_start ""')

        self.assertEqual(self.post_enabled_seen_by_runtime(), "false")

    def test_fallback_launch_honors_an_explicit_post_switch(self):
        self.run_installer_functions('service_start ""', post_enabled="true")

        self.assertEqual(self.post_enabled_seen_by_runtime(), "true")

    def test_with_systemd_the_instance_is_started_through_the_unit(self):
        self.run_installer_functions('install_systemd_template\nservice_start ""', systemd_running=True)

        calls = (self.work / "systemctl.log").read_text(encoding="utf-8").splitlines()
        self.assertIn(f"enable --now easyaiot-runtime-rk3588@{TASK_ID}.service", calls)
        # 走了 systemd 就不能再走 nohup 回退：那条路径的环境与单元无关
        self.assertFalse((self.work / "state" / "tasks" / f"{TASK_ID}.ini.env").exists())


if __name__ == "__main__":
    unittest.main()
