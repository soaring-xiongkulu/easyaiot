"""DVR 设备解析单元测试（无 DB）。"""
import pytest
from unittest.mock import patch

from app.services import dvr_device_resolver as resolver
from app.services.dvr_device_resolver import (
    parse_infer_stream_device_id,
    parse_task_stream_identity,
)


@pytest.mark.parametrize(
    'stream,expected',
    [
        ('infer_1781506220127821717_mdefault', '1781506220127821717'),
        ('infer_1781506220124766624_mdefault', '1781506220124766624'),
        ('infer_123_my_model', '123'),
        ('1781781474119258643', None),
        ('live/1781781474119258643', None),
        ('', None),
    ],
)
def test_parse_infer_stream_device_id(stream, expected):
    assert parse_infer_stream_device_id(stream) == expected


@pytest.mark.parametrize(
    'stream,expected',
    [
        ('t101_CAM-001', (101, 'CAM-001')),
        ('t202_factory-gate_a1b2c3d4', (202, 'factory-gate_a1b2c3d4')),
        ('infer_CAM-001_mdefault', (None, None)),
        ('', (None, None)),
    ],
)
def test_parse_task_stream_identity(stream, expected):
    assert parse_task_stream_identity(stream) == expected


def test_resolve_task_identity_from_dvr_path_when_hook_stream_missing():
    device = object()

    def resolve_task_stream(stream):
        if stream == 't101_CAM-001':
            return 101, 'CAM-001', device
        return None, None, None

    with patch.object(
        resolver,
        '_resolve_task_stream_device',
        side_effect=resolve_task_stream,
    ) as resolve_task_stream:
        result = resolver.resolve_stream_identity_from_hook(
            '',
            '/data/playbacks/ai/t101_CAM-001/2026-08-12/segment.flv',
        )

    assert result == (101, 'CAM-001', device)
    resolve_task_stream.assert_any_call('t101_CAM-001')
