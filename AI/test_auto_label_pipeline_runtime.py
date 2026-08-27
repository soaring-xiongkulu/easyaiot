import json
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from app.blueprints import auto_label
from app.services import auto_label_cluster_service
from app.utils import node_client


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class PipelineRuntimeTest(unittest.TestCase):
    def test_local_pipeline_filters_empty_annotations_by_default(self):
        task = MagicMock()
        task.dataset_id = 5
        task.pipeline_config = '{}'

        with patch.object(
            auto_label,
            '_download_dataset_image',
            return_value=(7, '/tmp/image.jpg', 640, 480),
        ), patch(
            'app.services.auto_label_orchestrator.is_task_paused_or_cancelled',
            return_value=False,
        ), patch(
            'app.services.auto_label_orchestrator.label_image_with_strategy',
            return_value=([], 'yolo'),
        ), patch(
            'app.services.auto_label_orchestrator._update_counters',
        ), patch(
            'app.services.auto_label_strategy.get_current_model_id',
            return_value=None,
        ), patch(
            'app.services.auto_label_dataset_writer.write_auto_label_result',
            return_value=('[]', 'deleted'),
        ) as write_result, patch.object(
            auto_label.db.session,
            'add',
        ), patch.object(
            auto_label.os.path,
            'exists',
            return_value=False,
        ):
            result = auto_label._sam_label_images(
                task,
                13,
                object(),
                'http://gateway.test',
                [{'id': 7}],
            )

        self.assertEqual(result, (0, 0))
        write_result.assert_called_once_with(
            'http://gateway.test',
            5,
            7,
            [],
            keep_annotated_images_only=True,
            timeout=10,
        )

    def test_dispatch_carries_existing_counters_into_restarted_worker(self):
        parent = MagicMock()
        parent.id = 13
        parent.dataset_id = 5
        parent.text_prompts = '[]'
        parent.annotation_type = 'rectangle'
        parent.confidence_threshold = 0.45
        parent.return_masks = False

        subtask = MagicMock()
        subtask.id = 2
        subtask.parent_task_id = parent.id
        subtask.frame_task_id = 4
        subtask.rtmp_url = 'rtmp://stream.test/live'
        subtask.config_json = '{}'
        subtask.captured_count = 6
        subtask.labeled_count = 27
        subtask.failed_count = 0

        parent_model = MagicMock()
        parent_model.query.get.return_value = parent

        with patch.object(
            auto_label_cluster_service,
            'AutoLabelTask',
            parent_model,
        ), patch.object(
            node_client,
            'allocate_node',
            return_value={'nodeId': 4, 'host': 'node.test', 'gpuIds': None},
        ), patch.object(
            node_client,
            'get_node',
            return_value=MagicMock(),
        ), patch.object(
            node_client,
            'deploy_workload',
            return_value={'pid': 123},
        ) as deploy_workload, patch.object(
            auto_label_cluster_service,
            'is_platform_node',
            return_value=False,
        ), patch.object(
            auto_label_cluster_service,
            'resolve_ai_bundle_python',
            return_value='/python',
        ), patch.object(
            auto_label_cluster_service.db.session,
            'commit',
        ):
            dispatched = auto_label_cluster_service.dispatch_subtask_to_node(subtask)

        self.assertTrue(dispatched)
        env = deploy_workload.call_args.kwargs['env']
        self.assertEqual(env['INITIAL_CAPTURED_COUNT'], '6')
        self.assertEqual(env['INITIAL_LABELED_COUNT'], '27')
        self.assertEqual(env['INITIAL_FAILED_COUNT'], '0')
        self.assertEqual(env['KEEP_ANNOTATED_IMAGES_ONLY'], 'true')

    def test_subtask_progress_counters_do_not_decrease_after_worker_restart(self):
        subtask = MagicMock()
        subtask.captured_count = 11
        subtask.labeled_count = 16
        subtask.failed_count = 2
        subtask.processed_images = 27

        subtask_model = MagicMock()
        subtask_model.query.get.return_value = subtask

        with patch.object(
            auto_label_cluster_service,
            'AutoLabelSubTask',
            subtask_model,
        ), patch.object(
            auto_label_cluster_service,
            '_aggregate_parent_tasks',
        ), patch.object(
            auto_label_cluster_service.db.session,
            'commit',
        ):
            auto_label_cluster_service.update_subtask_progress(
                2,
                {
                    'status': 'RUNNING',
                    'captured_count': 1,
                    'labeled_count': 3,
                    'failed_count': 0,
                    'processed_images': 4,
                },
            )

        self.assertEqual(subtask.captured_count, 11)
        self.assertEqual(subtask.labeled_count, 16)
        self.assertEqual(subtask.failed_count, 2)
        self.assertEqual(subtask.processed_images, 27)

    def test_cluster_parent_stays_pending_when_dispatch_fails(self):
        class FakeApp:
            @contextmanager
            def app_context(self):
                yield

        parent = MagicMock()
        parent.id = 13
        parent.status = 'PENDING'
        parent.started_at = None

        subtask = MagicMock()
        subtask.parent_task_id = parent.id
        subtask.assigned_node_id = None

        subtask_model = MagicMock()
        subtask_model.query.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [subtask]
        parent_model = MagicMock()
        parent_model.query.get.return_value = parent

        with patch.object(auto_label_cluster_service, 'AutoLabelSubTask', subtask_model), patch.object(
            auto_label_cluster_service,
            'AutoLabelTask',
            parent_model,
        ), patch.object(
            auto_label_cluster_service,
            'dispatch_subtask_to_node',
            return_value=False,
        ), patch.object(
            auto_label_cluster_service,
            '_aggregate_parent_tasks',
        ), patch.object(
            auto_label_cluster_service.db.session,
            'commit',
        ):
            dispatched = auto_label_cluster_service.process_queue_once(FakeApp())

        self.assertEqual(dispatched, 0)
        self.assertEqual(parent.status, 'PENDING')
        self.assertIsNone(parent.started_at)

    def test_fetch_frame_tasks_resolves_selected_gb28181_stream(self):
        frame_task_response = FakeResponse({
            'code': 0,
            'data': {
                'list': [
                    {
                        'id': 4,
                        'taskName': 'GB camera',
                        'taskType': 1,
                        'deviceId': '33080300002000251117',
                        'channelId': '33080351001310314002',
                        'rtmpUrl': '',
                    },
                    {
                        'id': 5,
                        'taskName': 'unselected camera',
                        'taskType': 0,
                        'rtmpUrl': 'rtsp://example.test/unselected',
                    },
                ],
            },
        })
        inference_input_response = FakeResponse({
            'code': 0,
            'data': {
                'resolved_source': 'rtsp://media.test/selected',
            },
        })

        with patch.dict(
            auto_label.os.environ,
            {'AUTO_LABEL_STREAM_RESOLVE_TIMEOUT_SEC': 'invalid'},
        ), patch.object(
            auto_label.requests,
            'get',
            side_effect=[frame_task_response, inference_input_response],
        ) as request_get:
            tasks = auto_label._fetch_frame_tasks(
                'http://gateway.test',
                6,
                frame_task_ids=[4],
                resolve_streams=True,
            )

        self.assertEqual([task['id'] for task in tasks], [4])
        self.assertEqual(tasks[0]['rtmpUrl'], 'rtsp://media.test/selected')
        self.assertEqual(request_get.call_count, 2)
        self.assertIn(
            '/admin-api/video/camera/device/'
            'gb28181_33080300002000251117_33080351001310314002/inference-input',
            request_get.call_args_list[1].args[0],
        )

    def test_pipeline_log_uses_shanghai_time(self):
        class Task:
            id = 0
            pipeline_config = '{}'

        task = Task()
        auto_label._pipeline_log(task, 'timezone-probe')

        logged = datetime.fromisoformat(
            json.loads(task.pipeline_config)['logs'][-1]['time']
        )
        expected = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
        self.assertLess(abs((expected - logged).total_seconds()), 5)

    def test_platform_worker_command_runs_inside_ai_container(self):
        command, deploy_env = auto_label_cluster_service._platform_worker_command(
            {
                'AI_ROOT': '/opt/easyaiot/AI',
                'DATASET_ID': '5',
                'JWT_TOKEN': 'secret-token',
            },
            gpu_ids='2',
        )

        self.assertEqual(command[:4], ['docker', 'exec', '-w', '/app/services/auto_label_worker'])
        self.assertEqual(
            command[-3:],
            ['ai-service', '/opt/conda/bin/python', '/app/services/auto_label_worker/run_worker.py'],
        )
        self.assertNotIn('/opt/easyaiot/AI/.bundles/ai_service/run-python.sh', command)
        self.assertNotIn('secret-token', command)
        self.assertEqual(deploy_env['AI_ROOT'], '/app')
        self.assertEqual(deploy_env['CUDA_VISIBLE_DEVICES'], '2')


if __name__ == '__main__':
    unittest.main()
