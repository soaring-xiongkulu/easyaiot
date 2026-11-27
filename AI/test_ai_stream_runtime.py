import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.utils import ai_env
from app.utils.pose_rtsp_pipeline import PoseRtspStreamPipeline
from app.utils.rtsp_stream_pipeline import RtspStreamPipeline
from app.utils.srs_host import resolve_srs_play_host, resolve_srs_publish_host


class TestAiEnvironmentLoading(unittest.TestCase):
    def test_container_keeps_compose_database_over_loopback_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, '.env').write_text(
                'DATABASE_URL=postgresql://postgres:secret@localhost:5432/ai\n',
                encoding='utf-8',
            )
            with patch.dict(
                os.environ,
                {'DATABASE_URL': 'postgresql://postgres:secret@postgres-server:5432/ai'},
                clear=True,
            ), patch.object(ai_env, 'ai_root_dir', return_value=tmp), patch.object(
                ai_env,
                '_running_in_container',
                return_value=True,
            ):
                ai_env.load_ai_env(override=True)
                self.assertEqual(
                    os.environ['DATABASE_URL'],
                    'postgresql+psycopg2://postgres:secret@postgres-server:5432/ai',
                )

    def test_non_container_keeps_dotenv_override_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, '.env').write_text(
                'DATABASE_URL=postgresql://postgres:secret@localhost:5432/ai\n',
                encoding='utf-8',
            )
            with patch.dict(
                os.environ,
                {'DATABASE_URL': 'postgresql://postgres:secret@postgres-server:5432/ai'},
                clear=True,
            ), patch.object(ai_env, 'ai_root_dir', return_value=tmp), patch.object(
                ai_env,
                '_running_in_container',
                return_value=False,
            ):
                ai_env.load_ai_env(override=True)
                self.assertEqual(
                    os.environ['DATABASE_URL'],
                    'postgresql+psycopg2://postgres:secret@localhost:5432/ai',
                )


class TestSrsHostResolution(unittest.TestCase):
    def test_explicit_publish_host_has_priority(self) -> None:
        self.assertEqual(
            resolve_srs_publish_host('srs-explicit', probe=lambda *_: False),
            'srs-explicit',
        )

    def test_bridge_service_is_selected_when_loopback_is_closed(self) -> None:
        checked: list[str] = []

        def probe(host: str, _port: int) -> bool:
            checked.append(host)
            return host == 'srs-server'

        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_srs_publish_host(probe=probe), 'srs-server')
        self.assertEqual(checked[:3], ['127.0.0.1', 'localhost', 'srs-server'])

    def test_browser_play_host_never_inherits_publish_service_name(self) -> None:
        with patch.dict(
            os.environ,
            {'MODEL_AI_SRS_HOST': 'srs-server'},
            clear=True,
        ):
            self.assertEqual(resolve_srs_play_host(), '127.0.0.1')


class TestRealtimePushFailure(unittest.TestCase):
    @staticmethod
    def _dead_process():
        return SimpleNamespace(poll=lambda: 111, stdin=None)

    def test_detection_pipeline_reports_ffmpeg_exit(self) -> None:
        pipeline = RtspStreamPipeline(
            reader=SimpleNamespace(fps=25),
            ffmpeg_process=self._dead_process(),
            model=object(),
            detect_config={},
            stop_event=threading.Event(),
        )
        pipeline._fixed_rate_push_worker()
        self.assertTrue(pipeline._push_failure.is_set())
        self.assertIn('exit=111', pipeline._push_error or '')

    def test_pose_pipeline_reports_ffmpeg_exit(self) -> None:
        pipeline = PoseRtspStreamPipeline(
            reader=SimpleNamespace(fps=25),
            ffmpeg_process=self._dead_process(),
            model=object(),
            stop_event=threading.Event(),
        )
        pipeline._fixed_rate_push_worker()
        self.assertTrue(pipeline._push_failure.is_set())
        self.assertIn('exit=111', pipeline._push_error or '')


if __name__ == '__main__':
    unittest.main()
