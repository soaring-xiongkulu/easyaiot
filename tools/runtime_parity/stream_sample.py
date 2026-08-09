"""Overlay / RTMP stream sampling helpers for G-4.4 (L_overlay / L_stream)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _ffprobe_bin(root: Optional[Path] = None) -> Optional[Path]:
    env = (os.environ.get("FFPROBE_BIN") or "").strip()
    if env and Path(env).is_file():
        return Path(env)
    which = shutil.which("ffprobe")
    if which:
        return Path(which)
    candidates: List[Path] = []
    if root is not None:
        candidates.extend(
            [
                root / "RUNTIME" / "vendor" / "win-x64" / "_conda_ffmpeg4" / "Library" / "bin" / "ffprobe.exe",
                root / "RUNTIME" / "vendor" / "win-x64" / "conda-pkgs" / "ffmpeg" / "Library" / "bin" / "ffprobe.exe",
            ]
        )
    for p in candidates:
        if p.is_file():
            return p
    return None


def parse_ffprobe_stream(probe: Dict[str, Any]) -> Dict[str, Any]:
    """Extract video stream width/height/fps/bitrate from ffprobe JSON."""
    streams = probe.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    fmt = probe.get("format") or {}
    if video is None:
        return {
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "bitrate_kbps": 0.0,
            "codec_name": "",
            "gray_frame_count": 0,
        }

    fps = 0.0
    afr = str(video.get("avg_frame_rate") or "0/0")
    if "/" in afr:
        num, den = afr.split("/", 1)
        try:
            n, d = float(num), float(den)
            if d > 0:
                fps = n / d
        except ValueError:
            fps = 0.0
    if fps <= 0:
        rfr = str(video.get("r_frame_rate") or "0/0")
        if "/" in rfr:
            num, den = rfr.split("/", 1)
            try:
                n, d = float(num), float(den)
                if d > 0:
                    fps = n / d
            except ValueError:
                fps = 0.0

    br = video.get("bit_rate") or fmt.get("bit_rate") or 0
    try:
        bitrate_kbps = float(br) / 1000.0
    except (TypeError, ValueError):
        bitrate_kbps = 0.0

    return {
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": round(fps, 3),
        "bitrate_kbps": round(bitrate_kbps, 1),
        "codec_name": str(video.get("codec_name") or ""),
        "gray_frame_count": 0,
    }


def ffprobe_url(url: str, *, root: Optional[Path] = None, timeout: float = 12.0) -> Optional[Dict[str, Any]]:
    """Run ffprobe against a live RTMP/HTTP-FLV URL; return parsed video fields or None."""
    bin_path = _ffprobe_bin(root)
    if bin_path is None:
        return None
    cmd = [
        str(bin_path),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        url,
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return None
    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return parse_ffprobe_stream(raw)


def overlay_from_parity(parity: Dict[str, Any]) -> Dict[str, Any]:
    ov = parity.get("overlay") or {}
    return {
        "sample_count": int(ov.get("sample_count") or 0),
        "drawn_count": int(ov.get("drawn_count") or 0),
        "p50_latency_ms": float(ov.get("p50_latency_ms") or 0.0),
        "p95_latency_ms": float(ov.get("p95_latency_ms") or 0.0),
        "frames": ov.get("frames") or [],
    }


def stream_from_parity(parity: Dict[str, Any]) -> Dict[str, Any]:
    st = parity.get("stream") or {}
    return {
        "rtmp_url": str(st.get("rtmp_url") or ""),
        "width": int(st.get("width") or 0),
        "height": int(st.get("height") or 0),
        "fps": float(st.get("fps") or 0),
        "bitrate_kbps": float(st.get("bitrate_kbps") or 0),
        "pushed_ok": int(st.get("pushed_ok") or 0),
        "pushed_fail": int(st.get("pushed_fail") or 0),
        "meta_set": bool(st.get("meta_set")),
        "gray_frame_count": int(st.get("gray_frame_count") or 0),
        "codec_name": str(st.get("codec_name") or ""),
        "quality_profile": str(st.get("quality_profile") or ""),
        "nvenc_requested": bool(st.get("nvenc_requested")),
        "nvenc_fallback": bool(st.get("nvenc_fallback")),
        "quality_downgraded": bool(st.get("quality_downgraded")),
    }


def synthetic_overlay_oracle(*, frame_skip: int = 4, fps: float = 25.0) -> Dict[str, Any]:
    """
    Oracle smoke baseline for overlay latency.

    Dual-queue 1:1 is not required for G-4.4; use a deterministic P95 baseline
    approximating Python overlay worker delay (frame_skip * frame_period * 0.5).
    """
    frame_ms = 1000.0 / max(1.0, fps)
    # Conservative python-side visible delay stub (ms)
    p50 = frame_skip * frame_ms * 0.35
    p95 = frame_skip * frame_ms * 0.75
    return {
        "sample_count": 40,
        "drawn_count": 40,
        "p50_latency_ms": round(p50, 2),
        "p95_latency_ms": round(p95, 2),
        "frames": [],
        "_note": "oracle_smoke overlay latency stub (not dual-queue replay)",
    }


def synthetic_stream_oracle(*, width: int = 768, height: int = 432, fps: int = 12, bitrate_kbps: int = 2500) -> Dict[str, Any]:
    """Expected RTMP encoder profile matching RUNTIME RTMPEncoder + Intel sample media."""
    return {
        "rtmp_url": "rtmp://127.0.0.1:1935/live/parity_oracle_stub",
        "width": width,
        "height": height,
        "fps": float(fps),
        "bitrate_kbps": float(bitrate_kbps),
        "pushed_ok": 100,
        "pushed_fail": 0,
        "gray_frame_count": 0,
        "codec_name": "h264",
        "ffprobe": {
            "width": width,
            "height": height,
            "fps": float(fps),
            "bitrate_kbps": float(bitrate_kbps),
            "codec_name": "h264",
            "gray_frame_count": 0,
        },
        "_note": "oracle_smoke expected stream profile (SRS + RTMPEncoder + media fps)",
    }


def http_flv_url_for_rtmp(rtmp_url: str) -> str:
    """Map rtmp://host:1935/live/name → http://host:8080/live/name.flv (SRS default)."""
    # rtmp://127.0.0.1:1935/live/foo → http://127.0.0.1:8080/live/foo.flv
    if not rtmp_url.startswith("rtmp://"):
        return ""
    rest = rtmp_url[len("rtmp://") :]
    host_port, _, path = rest.partition("/")
    host = host_port.split(":")[0] if host_port else "127.0.0.1"
    stream_path = path if path else "live/stream"
    return f"http://{host}:8080/{stream_path}.flv"


def rtmp_stream_name(case_id: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in case_id)
    return f"parity_{safe}"
