import types
import unittest
from datetime import timedelta
from unittest.mock import patch


class AlgorithmIngressScheduleValidationTest(unittest.TestCase):
    @staticmethod
    def _device(device_id: str, ingress_node_id=None):
        return types.SimpleNamespace(id=device_id, ingress_node_id=ingress_node_id)

    def test_edge_devices_on_same_node_accept_matching_target(self):
        from app.services.algorithm_task_service import (
            validate_algorithm_device_ingress_schedule,
        )

        validate_algorithm_device_ingress_schedule(
            [self._device('camera-a', 5), self._device('camera-b', 5)],
            'node',
            5,
        )

    def test_devices_on_different_edge_nodes_are_rejected(self):
        from app.services.algorithm_task_service import (
            validate_algorithm_device_ingress_schedule,
        )

        with self.assertRaisesRegex(ValueError, '不同接入节点'):
            validate_algorithm_device_ingress_schedule(
                [self._device('camera-a', 5), self._device('camera-b', 6)],
                'node',
                5,
            )

    def test_main_and_edge_devices_are_rejected(self):
        from app.services.algorithm_task_service import (
            validate_algorithm_device_ingress_schedule,
        )

        with self.assertRaisesRegex(ValueError, '不同接入节点'):
            validate_algorithm_device_ingress_schedule(
                [self._device('camera-main'), self._device('camera-edge', 5)],
                'node',
                5,
            )

    def test_edge_device_requires_matching_explicit_node(self):
        from app.services.algorithm_task_service import (
            validate_algorithm_device_ingress_schedule,
        )

        with self.assertRaisesRegex(ValueError, '调度策略必须为指定节点'):
            validate_algorithm_device_ingress_schedule(
                [self._device('camera-a', 5)],
                'auto',
                None,
            )

        with self.assertRaisesRegex(ValueError, '目标节点必须选择该接入节点'):
            validate_algorithm_device_ingress_schedule(
                [self._device('camera-a', 5)],
                'node',
                6,
            )

    def test_main_ingress_devices_keep_existing_schedule_options(self):
        from app.services.algorithm_task_service import (
            validate_algorithm_device_ingress_schedule,
        )

        for policy, target in [('local', None), ('auto', None), ('node', 5)]:
            with self.subTest(policy=policy):
                validate_algorithm_device_ingress_schedule(
                    [self._device('camera-main')],
                    policy,
                    target,
                )


class StreamForwardRuntimeRoutingTest(unittest.TestCase):
    def test_remote_cpp_task_does_not_require_control_plane_runtime(self):
        from app.services import stream_forward_launcher_service as launcher

        task = types.SimpleNamespace(executor='cpp')
        with patch.object(launcher, '_use_remote_deploy', return_value=True):
            self.assertFalse(launcher._requires_local_runtime(task))

    def test_local_cpp_task_still_requires_runtime(self):
        from app.services import stream_forward_launcher_service as launcher

        task = types.SimpleNamespace(executor='cpp')
        with patch.object(launcher, '_use_remote_deploy', return_value=False):
            self.assertTrue(launcher._requires_local_runtime(task))


class AlgorithmDeploymentCancellationTest(unittest.TestCase):
    def test_sharded_deploy_cleans_new_workload_if_stop_wins_race(self):
        from app.services import algorithm_task_cluster_service as cluster
        from app.services import algorithm_task_launcher_service as launcher

        task = types.SimpleNamespace(
            id=19,
            devices=[types.SimpleNamespace(id='camera-a')],
        )
        deployment = {
            'node_id': 5,
            'workload_id': '19:camera-a',
            'local': False,
        }
        with (
            patch.object(launcher, '_ensure_task_models_on_cluster', return_value=(True, 'ok')),
            patch.object(cluster, '_task_is_enabled', side_effect=[True, True, True, False]),
            patch.object(cluster, '_should_spread_shards', return_value=False),
            patch.object(cluster, '_deploy_shard_for_schedule', return_value=deployment),
            patch.object(cluster, '_stop_pending_deployments') as stop_pending,
        ):
            result = cluster.deploy_sharded_algorithm_task(19, task)

        self.assertFalse(result[0])
        self.assertIn('停用', result[1])
        stop_pending.assert_called_once_with([deployment])

    def test_pending_remote_shard_is_stopped_when_task_is_disabled(self):
        from app.services import algorithm_task_cluster_service as cluster

        deployment = {
            'node_id': 5,
            'workload_id': '19:camera-a',
            'local': False,
        }
        with patch.object(cluster, 'stop_remote_workload') as stop_remote:
            cluster._stop_pending_deployments([deployment])
        stop_remote.assert_called_once_with(5, '19:camera-a')

    def test_pending_local_shard_is_stopped_when_task_is_disabled(self):
        from app.services import algorithm_task_cluster_service as cluster

        deployment = {
            'workload_id': '19:camera-a',
            'local': True,
        }
        with patch.object(cluster, '_stop_local_shard') as stop_local:
            cluster._stop_pending_deployments([deployment])
        stop_local.assert_called_once_with('19:camera-a')


class RemoteAlgorithmHeartbeatRoutingTest(unittest.TestCase):
    @staticmethod
    def _remote_cpp_task():
        return types.SimpleNamespace(
            id=4,
            task_type='realtime',
            executor='cpp',
            schedule_policy='node',
            target_node_id=5,
            prefer_gpu=False,
            runtime_control_port=None,
            devices=[types.SimpleNamespace(id='camera-a')],
        )

    def test_remote_cpp_runtime_ini_uses_control_plane_heartbeat_url(self):
        from app.services import algorithm_task_cluster_service as cluster
        from app.services import algorithm_task_launcher_service as launcher
        from app.services import runtime_config_service as runtime_config
        from app.utils import node_client

        task = self._remote_cpp_task()
        heartbeat_url = 'http://192.0.2.10:6000/video/algorithm/heartbeat/realtime'
        with (
            patch.object(launcher, '_ensure_task_models_on_cluster', return_value=(True, 'ok')),
            patch.object(cluster, 'use_device_level_schedule', return_value=False),
            patch.object(node_client, 'allocate_node', return_value={
                'nodeId': 5,
                'host': '192.0.2.20',
                'gpuIds': '',
            }),
            patch.object(node_client, 'check_runtime_cpp_ready', return_value={
                'runtimeReady': True,
            }),
            patch.object(node_client, 'deploy_workload', return_value={'pid': 12345}),
            patch.object(
                launcher,
                '_build_task_deploy_env',
                return_value={'VIDEO_HEARTBEAT_URL': heartbeat_url},
            ),
            patch.object(
                runtime_config,
                'generate_runtime_ini_content',
                return_value=('/tmp/runtime.ini', '[video_task]\n'),
            ) as generate_ini,
            patch.object(launcher.db.session, 'commit'),
            patch.object(cluster, '_task_is_enabled', return_value=True),
        ):
            result = launcher._deploy_task_on_remote_node(4, task)

        self.assertTrue(result[0])
        self.assertEqual(generate_ini.call_args.kwargs['heartbeat_url'], heartbeat_url)

    def test_single_remote_deploy_cleans_new_workload_if_stop_wins_race(self):
        from app.services import algorithm_task_cluster_service as cluster
        from app.services import algorithm_task_launcher_service as launcher
        from app.services import runtime_config_service as runtime_config
        from app.utils import node_client

        task = self._remote_cpp_task()
        with (
            patch.object(launcher, '_ensure_task_models_on_cluster', return_value=(True, 'ok')),
            patch.object(cluster, 'use_device_level_schedule', return_value=False),
            patch.object(cluster, '_task_is_enabled', return_value=False),
            patch.object(cluster, 'stop_remote_workload') as stop_remote,
            patch.object(node_client, 'allocate_node', return_value={
                'nodeId': 5,
                'host': '192.0.2.20',
                'gpuIds': '',
            }),
            patch.object(node_client, 'check_runtime_cpp_ready', return_value={
                'runtimeReady': True,
            }),
            patch.object(node_client, 'deploy_workload', return_value={'pid': 12345}),
            patch.object(
                launcher,
                '_build_task_deploy_env',
                return_value={'VIDEO_HEARTBEAT_URL': 'http://192.0.2.10:6000/heartbeat'},
            ),
            patch.object(
                runtime_config,
                'generate_runtime_ini_content',
                return_value=('/tmp/runtime.ini', '[video_task]\n'),
            ),
            patch.object(launcher.db.session, 'commit') as commit,
        ):
            result = launcher._deploy_task_on_remote_node(4, task)

        self.assertFalse(result[0])
        self.assertIn('停用', result[1])
        stop_remote.assert_called_once_with(5, '4')
        commit.assert_not_called()


class RemoteRuntimeModelPathTest(unittest.TestCase):
    def test_builtin_model_uses_remote_runtime_path_for_cluster_deploy(self):
        from app.services import runtime_config_service as runtime_config

        model_path, names_path = runtime_config._resolve_single_model_path(
            -1,
            prefer_cluster=True,
            default_names=runtime_config.Path('/local/RUNTIME/models/coco.names'),
        )

        self.assertEqual(model_path, '/opt/easyaiot/RUNTIME/models/yolo11n.onnx')
        self.assertEqual(names_path, '/opt/easyaiot/RUNTIME/models/coco.names')


class AlgorithmSynchronousRemoteStopTest(unittest.TestCase):
    def test_remote_workload_is_stopped_before_background_teardown(self):
        from app.services import algorithm_task_launcher_service as launcher
        from app.services import algorithm_task_service as service

        task = types.SimpleNamespace(
            id=4,
            node_id=5,
            service_process_id=844415,
            run_status='running',
            device_deployments=None,
        )
        with (
            patch.object(launcher, '_stop_remote_task') as stop_remote,
            patch.object(service.db.session, 'commit') as commit,
        ):
            stopped = service._stop_remote_workload_before_background_teardown(task)

        self.assertTrue(stopped)
        stop_remote.assert_called_once_with(4, 5)
        self.assertIsNone(task.node_id)
        self.assertIsNone(task.service_process_id)
        self.assertEqual(task.run_status, 'stopped')
        commit.assert_called_once_with()

    def test_selected_edge_is_used_when_persisted_runtime_node_is_missing(self):
        from app.services import algorithm_task_launcher_service as launcher
        from app.services import algorithm_task_service as service

        task = types.SimpleNamespace(
            id=4,
            node_id=None,
            target_node_id=5,
            schedule_policy='node',
            service_process_id=844415,
            run_status='running',
            device_deployments=None,
        )
        with (
            patch.object(launcher, '_stop_remote_task') as stop_remote,
            patch.object(service.db.session, 'commit'),
        ):
            stopped = service._stop_remote_workload_before_background_teardown(task)

        self.assertTrue(stopped)
        stop_remote.assert_called_once_with(4, 5)

    def test_local_task_does_not_use_stale_target_node_for_cleanup(self):
        from app.services import algorithm_task_launcher_service as launcher

        task = types.SimpleNamespace(
            node_id=None,
            target_node_id=5,
            schedule_policy='local',
        )

        self.assertIsNone(launcher._resolve_remote_task_node_id(task))


class AlgorithmStartFailureStateTest(unittest.TestCase):
    def test_failed_start_is_disabled_and_reports_the_failure(self):
        from app.services import algorithm_task_service as service

        task = types.SimpleNamespace(
            id=4,
            is_enabled=True,
            run_status='running',
            exception_reason=None,
            updated_at=None,
        )
        with (
            patch.object(service, '_stop_remote_workload_before_background_teardown') as stop_remote,
            patch.object(service.db.session, 'commit') as commit,
        ):
            service._rollback_failed_algorithm_start(task, 'Agent 下发失败')

        self.assertFalse(task.is_enabled)
        self.assertEqual(task.run_status, 'stopped')
        self.assertEqual(task.exception_reason, 'Agent 下发失败')
        stop_remote.assert_called_once_with(task)
        commit.assert_called_once_with()


class AlertRuntimeTimestampTest(unittest.TestCase):
    def test_runtime_utc_timestamp_is_converted_to_shanghai_time(self):
        from app.services.alert_service import _parse_alert_time

        value = _parse_alert_time('2026-08-26T15:20:30Z')

        self.assertEqual('2026-08-26 23:20:30', value.strftime('%Y-%m-%d %H:%M:%S'))
        self.assertEqual(timedelta(hours=8), value.utcoffset())


if __name__ == '__main__':
    unittest.main()
