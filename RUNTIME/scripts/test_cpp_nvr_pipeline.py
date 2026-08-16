#!/usr/bin/env python3
"""C++ RUNTIME 链路脚本回归（不依赖浏览器 / WEB UI）。

覆盖：
  1) task_type=forward  推流转发 → SRS live/{device}
  2) task_type=realtime 实时算法 → SRS ai/{device}（YOLO 带框）
  3) task_type=snap     抓拍算法（空 cron → 按 frame_skip 秒周期）
  4) task_type=patrol   巡检算法（多路轮巡）

默认 RTSP（勿把密码写进仓库）：
  export NVR_PASS='***'
  # 或整条：export NVR_RTSP='rtsp://user:pass@host:554/Streaming/Channels/101'

依赖：
  - 本机 SRS（:1935/:8080/:1985）
  - 脚本会自动 mock SRS on_publish（默认 :48080）；Gateway 已起时加 --skip-srs-hook-mock

用法：
  python3 RUNTIME/scripts/test_cpp_nvr_pipeline.py
  python3 RUNTIME/scripts/test_cpp_nvr_pipeline.py --only forward,realtime
  python3 RUNTIME/scripts/test_cpp_nvr_pipeline.py --keep  # 结束后不杀进程

退出码：0 全部通过；1 部分失败；2 环境/参数错误。
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = ROOT / "RUNTIME"
DEFAULT_BIN = RUNTIME_DIR / "build" / "RUNTIME"
DEFAULT_MODEL = RUNTIME_DIR / "models" / "yolo11n.onnx"
DEFAULT_NAMES = RUNTIME_DIR / "models" / "yolo11n.names"
DEFAULT_CONDA_LIB = Path.home() / "miniconda3/envs/easyaiot-runtime/lib"
DEFAULT_ORT_LIB = ROOT / ".deps/onnxruntime-linux-x64-1.23.2/lib"


def _default_nvr_rtsp(channel: str) -> str:
    """优先 NVR_RTSP / NVR_RTSP2；否则用 NVR_USER/NVR_PASS/NVR_HOST 拼装（密码勿写入仓库）。"""
    env_key = "NVR_RTSP" if channel == "101" else "NVR_RTSP2"
    if os.getenv(env_key):
        return os.environ[env_key]
    user = os.getenv("NVR_USER", "admin")
    password = os.getenv("NVR_PASS", "")
    host = os.getenv("NVR_HOST", "10.200.231.1")
    if not password:
        return ""
    return (
        f"rtsp://{quote(user, safe='')}:{quote(password, safe='')}"
        f"@{host}:554/Streaming/Channels/{channel}"
    )


class _JsonOkHandler(BaseHTTPRequestHandler):
    """POST/GET → {"code":0}；子类可覆写 on_hit(path)。"""

    def on_hit(self, path: str) -> None:  # noqa: ARG002
        return

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        _ = self.rfile.read(length) if length else b""
        self.on_hit(self.path)
        body = b'{"code":0,"msg":null}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args):  # noqa: A003
        return


class MockHttpServer:
    """轻量 HTTP mock（心跳 / SRS on_publish 等）。"""

    def __init__(self, host: str, port: int, name: str = "mock"):
        self.host = host
        self.port = port
        self.name = name
        self.hits: List[Tuple[str, float]] = []
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> str:
        outer = self

        class Handler(_JsonOkHandler):
            def on_hit(self, path: str) -> None:
                outer.hits.append((path, time.time()))

        self._httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True, name=f"{self.name}-http"
        )
        self._thread.start()
        return f"http://{self.host}:{self.port}"

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()


# 兼容旧名
HeartbeatServer = MockHttpServer


def log(msg: str) -> None:
    print(msg, flush=True)


def http_get(url: str, timeout: float = 3.0, max_read: int = 64 * 1024) -> Tuple[int, bytes, str]:
    """GET；对流式响应只读前 max_read 字节（HTTP-FLV 不会 EOF）。"""
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            chunks: List[bytes] = []
            remain = max_read
            while remain > 0:
                piece = resp.read(min(8192, remain))
                if not piece:
                    break
                chunks.append(piece)
                remain -= len(piece)
                # 已拿到 FLV 头即可停，避免被长连接拖满 timeout
                blob = b"".join(chunks)
                if blob[:3] == b"FLV" and len(blob) >= 16:
                    break
            return resp.status, b"".join(chunks), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(4096) if e.fp else b"", ""
    except Exception as e:  # noqa: BLE001
        return -1, str(e).encode(), ""


def srs_streams(api: str = "http://127.0.0.1:1985") -> List[dict]:
    code, body, _ = http_get(f"{api.rstrip('/')}/api/v1/streams/", timeout=3)
    if code != 200:
        return []
    try:
        data = json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return []
    return list(data.get("streams") or [])


def probe_flv(url: str, timeout: float = 5.0, min_bytes: int = 16) -> Tuple[bool, str]:
    code, body, ctype = http_get(url, timeout=timeout, max_read=64 * 1024)
    if code == 200 and len(body) >= min_bytes and ("flv" in (ctype or "").lower() or body[:3] == b"FLV"):
        return True, f"HTTP {code} bytes={len(body)} ctype={ctype or '-'}"
    return False, f"HTTP {code} bytes={len(body)} ctype={ctype or '-'} body={body[:80]!r}"


def stream_active(app: str, name: str, api: str = "http://127.0.0.1:1985") -> bool:
    """SRS publish.active；兼容 name/stream 字段，短暂重试。"""
    for _ in range(5):
        for s in srs_streams(api):
            sid = s.get("name") or s.get("stream") or ""
            if s.get("app") == app and sid == name:
                pub = s.get("publish") or {}
                if pub.get("active"):
                    return True
        time.sleep(0.5)
    return False


def ensure_srs(api: str = "http://127.0.0.1:1985") -> None:
    code, body, _ = http_get(f"{api.rstrip('/')}/api/v1/versions", timeout=3)
    if code != 200:
        raise RuntimeError(f"SRS 不可用 ({api}): HTTP {code} {body[:120]!r}")


def start_srs_hook_mock(port: int = 48080) -> MockHttpServer:
    """SRS docker.conf 默认 on_publish → http://172.18.0.1:48080/...；未起 Gateway 时必须 mock。"""
    srv = MockHttpServer("0.0.0.0", port, name="srs-hook")
    try:
        srv.start()
    except OSError as e:
        raise RuntimeError(
            f"无法监听 :{port} 作为 SRS on_publish mock（{e}）。"
            "请确认 Gateway/VIDEO 未占用，或先关掉占用进程。"
        ) from e
    # 自检：宿主机 bridge IP（SRS host 网络也会走该地址）
    code, body, _ = http_get(f"http://127.0.0.1:{port}/", timeout=2)
    if code != 200:
        srv.stop()
        raise RuntimeError(f"SRS hook mock 自检失败: HTTP {code} {body[:80]!r}")
    return srv


def build_env(conda_lib: Path, ort_lib: Path) -> Dict[str, str]:
    env = os.environ.copy()
    ld = f"{conda_lib}:{ort_lib}"
    old = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = f"{ld}:{old}" if old else ld
    env["CONDA_PREFIX"] = str(conda_lib.parent)
    env["STREAM_FORWARD_FFMPEG"] = env.get("STREAM_FORWARD_FFMPEG") or "/usr/bin/ffmpeg"
    # OpenCV VideoCapture（snap/patrol）走 TCP RTSP，避免 UDP 丢包
    env["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = env.get(
        "OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp"
    )
    env["RUNTIME_FORCE_CPU"] = "1"
    env["USE_GPU"] = "false"
    return env


def write_ini(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def kill_pid(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(20):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def wait_log(log_path: Path, needles: List[str], timeout: float) -> Tuple[bool, str]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if log_path.exists():
            text = log_path.read_bytes().decode("utf-8", "replace")
            if all(n in text for n in needles):
                return True, text
        time.sleep(0.4)
    text = log_path.read_bytes().decode("utf-8", "replace") if log_path.exists() else ""
    return False, text


class RuntimeJob:
    def __init__(self, name: str, proc: subprocess.Popen, log_path: Path, ini_path: Path):
        self.name = name
        self.proc = proc
        self.log_path = log_path
        self.ini_path = ini_path

    @property
    def alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self) -> None:
        if self.alive:
            kill_pid(self.proc.pid)
        # 顺带清掉本任务拉起的 ffmpeg 子进程（按 ini 内 rtmp 名过滤太脆，按 ppid 更稳）
        try:
            out = subprocess.check_output(["ps", "-eo", "pid,ppid,args"], text=True)
            for line in out.splitlines():
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue
                pid_s, ppid_s, args = parts
                if ppid_s == str(self.proc.pid) and "ffmpeg" in args:
                    kill_pid(int(pid_s))
        except Exception:  # noqa: BLE001
            pass


def start_runtime(bin_path: Path, ini: Path, log_path: Path, env: Dict[str, str]) -> RuntimeJob:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(log_path, "wb")
    proc = subprocess.Popen(
        [str(bin_path), str(ini)],
        stdout=fp,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(RUNTIME_DIR),
    )
    return RuntimeJob(ini.stem, proc, log_path, ini)


def ini_forward(device_id: str, rtsp: str, heartbeat: str, control_port: int, work: Path) -> str:
    return f"""# auto-generated by test_cpp_nvr_pipeline.py
[video]
rtsp_url={rtsp}
rtmp_url=rtmp://127.0.0.1:1935/live/{device_id}
width=1920
height=1080
fps=25

[task]
id=forward_{device_id}
control_port={control_port}

[video_task]
device_id={device_id}
device_name=NVR-CH1-forward
task_type=forward
heartbeat_url={heartbeat}/video/stream-forward/heartbeat
heartbeat_interval_sec=10
log_path={work}/logs/forward_{device_id}
headless=true

[features]
enable_rtmp=true
enable_draw=false
enable_alarm=false

[ai]
enable=false
"""


def ini_algo(
    task_type: str,
    device_id: str,
    devices: List[Tuple[str, str, str]],
    rtsp_primary: str,
    heartbeat: str,
    control_port: int,
    work: Path,
    model: Path,
    names: Path,
    frame_skip: int = 8,
    cron: str = "",
    patrol_interval: int = 5,
) -> str:
    devices_json = json.dumps(
        [{"device_id": d, "device_name": n, "rtsp_url": u} for d, n, u in devices],
        ensure_ascii=False,
    )
    rtmp = f"rtmp://127.0.0.1:1935/ai/{device_id}"
    enable_rtmp = "true" if task_type == "realtime" else "false"
    enable_draw = "true" if task_type == "realtime" else "false"
    return f"""# auto-generated by test_cpp_nvr_pipeline.py — {task_type}
[video]
rtsp_url={rtsp_primary}
rtmp_url={rtmp}
width=1920
height=1080
fps=25

[ai]
enable=true
model_path={model}
classes_path={names}
threads=2
frame_skip={frame_skip}
prefer_gpu=false
force_cpu=true
prefer_hwaccel=false
force_soft_av=true

[alarm]
enable=false
confidence_threshold=0.45
cooldown_time=5
image_dir={work}/alerts/{task_type}

[task]
id={task_type}_{device_id}
control_port={control_port}

[video_task]
device_id={device_id}
device_name=NVR-{task_type}
task_type={task_type}
algorithm_name=detection
heartbeat_url={heartbeat}/video/algorithm/heartbeat/{task_type if task_type != 'snap' else 'snapshot'}
heartbeat_interval_sec=10
log_path={work}/logs/{task_type}_{device_id}
alert_image_dir={work}/alerts/{task_type}
algo_bus_transport=http
headless=true
frame_skip={frame_skip}
cron_expression={cron}
patrol_mode=pool
patrol_interval_sec={patrol_interval}
patrol_pool_size=2
devices_json={devices_json}

[features]
enable_rtmp={enable_rtmp}
enable_draw={enable_draw}
enable_alarm=false
"""


def run_case_forward(args, env, hb_base: str, work: Path) -> bool:
    log("\n=== CASE forward (C++ 推流转发) ===")
    device_id = "cpp_fwd_ch1"
    ini = work / "ini" / f"forward_{device_id}.ini"
    write_ini(
        ini,
        ini_forward(device_id, args.rtsp, hb_base, args.control_base, work),
    )
    job = start_runtime(args.bin, ini, work / "logs" / f"forward_{device_id}.log", env)
    try:
        ok_start, text = wait_log(
            job.log_path,
            ["RUNTIME service started successfully", "ffmpeg CLI copy relay"],
            timeout=20,
        )
        if not ok_start:
            # 兼容 libav remux 路径
            ok_start = "Forward-only copy relay mode" in text or "Output ready" in text
        live_ok = False
        detail = ""
        for _ in range(20):
            live_ok, detail = probe_flv(f"http://127.0.0.1:8080/live/{device_id}.flv", timeout=4)
            if live_ok:
                break
            if not job.alive:
                break
            time.sleep(1)
        active = stream_active("live", device_id)
        # HTTP-FLV 可读即视为推流成功；SRS API 作交叉校验
        passed = job.alive and live_ok
        log(
            f"  process={'alive' if job.alive else 'DEAD'} live={live_ok} ({detail}) "
            f"srs_active={active}"
        )
        if not passed:
            text = job.log_path.read_bytes().decode("utf-8", "replace")
            log("  --- log tail ---")
            log("\n".join(text.splitlines()[-25:]))
        return passed
    finally:
        if not args.keep:
            job.stop()


def run_case_realtime(args, env, hb_base: str, work: Path) -> bool:
    log("\n=== CASE realtime (C++ 实时算法) ===")
    device_id = "cpp_rt_ch1"
    devices = [(device_id, "NVR-CH1", args.rtsp)]
    ini = work / "ini" / f"realtime_{device_id}.ini"
    write_ini(
        ini,
        ini_algo(
            "realtime",
            device_id,
            devices,
            args.rtsp,
            hb_base,
            args.control_base + 1,
            work,
            args.model,
            args.names,
            frame_skip=8,
        ),
    )
    job = start_runtime(args.bin, ini, work / "logs" / f"realtime_{device_id}.log", env)
    try:
        ok_start, text = wait_log(
            job.log_path,
            ["RUNTIME service started successfully", "PIPELINE"],
            timeout=40,
        )
        # YOLO may log detections
        time.sleep(8)
        ai_ok = False
        detail = ""
        for _ in range(25):
            ai_ok, detail = probe_flv(f"http://127.0.0.1:8080/ai/{device_id}.flv", timeout=4)
            if ai_ok:
                break
            if not job.alive:
                break
            time.sleep(1)
        text = job.log_path.read_bytes().decode("utf-8", "replace")
        yolo = ("detections=" in text) or ("Model loaded" in text) or ("[YOLO]" in text)
        active = stream_active("ai", device_id)
        rtmp_ok = "RTMP encoder initialized successfully" in text or "Streaming enabled" in text
        passed = job.alive and ok_start and ai_ok and yolo
        log(
            f"  process={'alive' if job.alive else 'DEAD'} start={ok_start} "
            f"ai={ai_ok} ({detail}) srs_active={active} rtmp_init={rtmp_ok} yolo={yolo}"
        )
        if not passed:
            log("  --- log tail ---")
            log("\n".join(text.splitlines()[-30:]))
        return passed
    finally:
        if not args.keep:
            job.stop()


def run_case_snap(args, env, hb_base: str, work: Path) -> bool:
    log("\n=== CASE snap (C++ 抓拍算法) ===")
    device_id = "cpp_snap_ch1"
    devices = [(device_id, "NVR-CH1", args.rtsp)]
    ini = work / "ini" / f"snap_{device_id}.ini"
    # cron 为空 → SnapScheduler 按 frame_skip 秒周期抓拍
    write_ini(
        ini,
        ini_algo(
            "snap",
            device_id,
            devices,
            args.rtsp,
            hb_base,
            args.control_base + 2,
            work,
            args.model,
            args.names,
            frame_skip=3,
            cron="",
        ),
    )
    job = start_runtime(args.bin, ini, work / "logs" / f"snap_{device_id}.log", env)
    try:
        ok_start, text = wait_log(
            job.log_path, ["[SNAP] starting scheduler", "[SNAP] loop started"], timeout=40
        )
        ok_open, text = wait_log(job.log_path, ["[SNAP] opening stream"], timeout=30)
        # 空 cron：按 frame_skip=3s 周期；再等一轮确认无 open/read 失败刷屏
        time.sleep(6)
        text = job.log_path.read_bytes().decode("utf-8", "replace")
        open_ok = "[SNAP] opening stream" in text
        open_fail = text.count("[SNAP] open failed")
        read_fail = text.count("[SNAP] read failed")
        model_ok = ("Model loaded" in text) or ("[YOLO]" in text) or ("ORT" in text)
        passed = (
            job.alive
            and ok_start
            and ok_open
            and open_ok
            and model_ok
            and open_fail == 0
            and read_fail <= 1
        )
        log(
            f"  process={'alive' if job.alive else 'DEAD'} start={ok_start} "
            f"open={open_ok} model={model_ok} open_fail={open_fail} read_fail={read_fail}"
        )
        if not passed:
            log("  --- log tail ---")
            log("\n".join(text.splitlines()[-40:]))
        return passed
    finally:
        if not args.keep:
            job.stop()


def run_case_patrol(args, env, hb_base: str, work: Path) -> bool:
    log("\n=== CASE patrol (C++ 巡检算法) ===")
    device_id = "cpp_patrol"
    devices = [
        ("cpp_patrol_ch1", "NVR-CH1", args.rtsp),
        ("cpp_patrol_ch2", "NVR-CH2", args.rtsp2),
    ]
    ini = work / "ini" / f"patrol_{device_id}.ini"
    write_ini(
        ini,
        ini_algo(
            "patrol",
            device_id,
            devices,
            args.rtsp,
            hb_base,
            args.control_base + 3,
            work,
            args.model,
            args.names,
            frame_skip=8,
            patrol_interval=4,
        ),
    )
    job = start_runtime(args.bin, ini, work / "logs" / f"patrol_{device_id}.log", env)
    try:
        ok_start, text = wait_log(
            job.log_path,
            ["[PATROL] starting scheduler", "[PATROL] loop started"],
            timeout=40,
        )
        # pool 模式会打 "[PATROL] pool device=..."；等两路都出现
        ok_ch1, _ = wait_log(job.log_path, ["[PATROL] pool device=cpp_patrol_ch1"], timeout=25)
        ok_ch2, text = wait_log(job.log_path, ["[PATROL] pool device=cpp_patrol_ch2"], timeout=25)
        time.sleep(2)
        text = job.log_path.read_bytes().decode("utf-8", "replace")
        open_fail = text.count("[PATROL] open failed")
        model_ok = ("Model loaded" in text) or ("[YOLO]" in text) or ("ORT" in text)
        passed = (
            job.alive
            and ok_start
            and ok_ch1
            and ok_ch2
            and model_ok
            and open_fail == 0
        )
        log(
            f"  process={'alive' if job.alive else 'DEAD'} start={ok_start} "
            f"ch1={ok_ch1} ch2={ok_ch2} model={model_ok} open_fail={open_fail}"
        )
        if not passed:
            log("  --- log tail ---")
            log("\n".join(text.splitlines()[-40:]))
        return passed
    finally:
        if not args.keep:
            job.stop()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="C++ RUNTIME NVR pipeline regression")
    p.add_argument("--bin", type=Path, default=Path(os.getenv("RUNTIME_BIN", DEFAULT_BIN)))
    p.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    p.add_argument("--names", type=Path, default=DEFAULT_NAMES)
    p.add_argument("--conda-lib", type=Path, default=Path(os.getenv("RUNTIME_CONDA_LIB_HOST", DEFAULT_CONDA_LIB)))
    p.add_argument("--ort-lib", type=Path, default=Path(os.getenv("RUNTIME_ORT_LIB_HOST", DEFAULT_ORT_LIB)))
    p.add_argument("--rtsp", default=_default_nvr_rtsp("101"))
    p.add_argument("--rtsp2", default=_default_nvr_rtsp("201"))
    p.add_argument("--work", type=Path, default=Path("/tmp/easyaiot-cpp-pipeline-test"))
    p.add_argument("--only", default="forward,realtime,snap,patrol", help="逗号分隔用例")
    p.add_argument("--control-base", type=int, default=8201)
    p.add_argument("--hb-port", type=int, default=18600)
    p.add_argument(
        "--srs-hook-port",
        type=int,
        default=int(os.getenv("SRS_HOOK_PORT", "48080")),
        help="SRS on_publish mock 端口（默认 48080，与 docker.conf 一致）",
    )
    p.add_argument("--skip-srs-hook-mock", action="store_true", help="已有 Gateway/VIDEO 时跳过 mock")
    p.add_argument("--keep", action="store_true", help="结束后保留进程")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    only = {x.strip() for x in args.only.split(",") if x.strip()}

    if not args.bin.is_file() or not os.access(args.bin, os.X_OK):
        log(f"ERROR: RUNTIME 二进制不可执行: {args.bin}")
        return 2
    if not args.rtsp:
        log("ERROR: 未配置 NVR RTSP。请设置 NVR_RTSP 或 NVR_PASS（及可选 NVR_USER/NVR_HOST）")
        return 2
    if "patrol" in only and not args.rtsp2:
        log("ERROR: patrol 需要第二路 RTSP。请设置 NVR_RTSP2 或 NVR_PASS")
        return 2
    if not args.model.is_file():
        log(f"ERROR: 模型不存在: {args.model}")
        return 2
    if not args.conda_lib.is_dir() or not args.ort_lib.is_dir():
        log(f"ERROR: 依赖库目录缺失 conda={args.conda_lib} ort={args.ort_lib}")
        return 2

    try:
        ensure_srs()
    except RuntimeError as e:
        log(f"ERROR: {e}")
        return 2

    work: Path = args.work
    work.mkdir(parents=True, exist_ok=True)
    (work / "ini").mkdir(exist_ok=True)
    (work / "logs").mkdir(exist_ok=True)
    (work / "alerts").mkdir(exist_ok=True)

    hook: Optional[MockHttpServer] = None
    if not args.skip_srs_hook_mock:
        try:
            hook = start_srs_hook_mock(args.srs_hook_port)
            log(f"SRS on_publish mock: 0.0.0.0:{args.srs_hook_port}")
        except RuntimeError as e:
            log(f"ERROR: {e}")
            return 2

    hb = MockHttpServer("127.0.0.1", args.hb_port, name="heartbeat")
    hb_base = hb.start()
    log(f"heartbeat mock: {hb_base}")
    log(f"RUNTIME: {args.bin}")
    # 日志脱敏：隐藏 RTSP userinfo
    safe_rtsp = args.rtsp
    if "://" in safe_rtsp and "@" in safe_rtsp:
        scheme, rest = safe_rtsp.split("://", 1)
        safe_rtsp = f"{scheme}://***@{rest.split('@', 1)[-1]}"
    log(f"RTSP: {safe_rtsp}")

    env = build_env(args.conda_lib, args.ort_lib)
    results: Dict[str, bool] = {}

    try:
        if "forward" in only:
            results["forward"] = run_case_forward(args, env, hb_base, work)
        if "realtime" in only:
            results["realtime"] = run_case_realtime(args, env, hb_base, work)
        if "snap" in only:
            results["snap"] = run_case_snap(args, env, hb_base, work)
        if "patrol" in only:
            results["patrol"] = run_case_patrol(args, env, hb_base, work)
    finally:
        hb.stop()
        if hook:
            hook.stop()

    log("\n========== SUMMARY ==========")
    for k, v in results.items():
        log(f"  {k:10s}  {'PASS' if v else 'FAIL'}")
    log(f"  heartbeats received: {len(hb.hits)}")
    if hook:
        log(f"  srs hooks received: {len(hook.hits)}")
    log(f"  work dir: {work}")

    if not results:
        return 2
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
