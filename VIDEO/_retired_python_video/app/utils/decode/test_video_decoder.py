"""video_decoder 命令行与重连行为单元测试。"""
from __future__ import annotations

import os
from unittest import mock

from app.utils.decode.video_decoder import DecoderConfig, VideoDecoder, build_ffmpeg_decode_cmd


def test_vaapi_cmd_includes_hwaccel_output_format():
    cfg = DecoderConfig(rtsp_url="rtsp://x", width=1920, height=1080, hwaccel="vaapi")
    cmd = build_ffmpeg_decode_cmd(cfg)
    assert "-hwaccel_output_format" in cmd
    idx = cmd.index("-hwaccel_output_format")
    assert cmd[idx + 1] == "vaapi"


def test_decoder_is_opened_during_reconnect_window():
    cfg = DecoderConfig(rtsp_url="rtsp://x", width=64, height=64, reconnect=True)
    dec = VideoDecoder(cfg)
    dec.is_running = True
    dec.process = mock.Mock()
    dec.process.poll.return_value = 1
    dec.process.returncode = 1
    assert dec.isOpened() is True


def test_decoder_not_opened_when_read_failed():
    cfg = DecoderConfig(rtsp_url="rtsp://x", width=64, height=64, reconnect=True)
    dec = VideoDecoder(cfg)
    dec.is_running = True
    dec.read_failed = True
    assert dec.isOpened() is False


def test_maybe_downgrade_hwaccel_after_repeated_failures(monkeypatch):
    monkeypatch.delenv("AI_DECODE_HWACCEL", raising=False)
    cfg = DecoderConfig(rtsp_url="rtsp://x", width=64, height=64, hwaccel="vaapi")
    dec = VideoDecoder(cfg)
    dec.stats["hwaccel"] = "vaapi"
    dec.stats["hwaccel_failures"] = 2
    assert dec._maybe_downgrade_hwaccel() is True
    assert dec.stats["hwaccel"] == "none"
    assert "hwaccel_output_format" not in " ".join(dec.ffmpeg_args)
