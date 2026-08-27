import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch


class PinnedStreamForwardRecoveryTest(unittest.TestCase):
    def test_stale_heartbeat_redeploys_on_the_pinned_online_node(self):
        from app.services import stream_forward_launcher_service as launcher

        task = types.SimpleNamespace(
            id=4,
            is_enabled=True,
            schedule_policy='node',
            target_node_id=5,
            service_last_heartbeat=datetime.utcnow() - timedelta(minutes=5),
            devices=[types.SimpleNamespace(id='camera-a')],
        )
        deployment = {
            'device_ids': ['camera-a'],
            'node_id': 5,
            'host': '192.0.2.20',
            'workload_id': '4',
        }
        replacement = {**deployment, 'pid': 12345}
        fake_model = types.SimpleNamespace(
            query=types.SimpleNamespace(get=lambda _task_id: task),
        )

        with (
            patch.object(launcher, 'StreamForwardTask', fake_model),
            patch.object(launcher, '_use_remote_deploy', return_value=True),
            patch.object(launcher, '_parse_device_deployments', return_value=[deployment]),
            patch.object(launcher, '_is_compute_node_online', return_value=True),
            patch.object(
                launcher,
                '_deploy_shard_with_workload_id',
                return_value=replacement,
            ) as deploy,
            patch.object(launcher, '_apply_task_service_fields_from_deployments') as apply_fields,
            patch.object(launcher.db.session, 'commit') as commit,
        ):
            migrated = launcher.migrate_unhealthy_stream_forward_task(4)

        self.assertEqual(migrated, 1)
        deploy.assert_called_once_with(
            4,
            task,
            ['camera-a'],
            '4',
            shard_index=0,
            fresh_allocate=True,
        )
        apply_fields.assert_called_once_with(task, [replacement])
        commit.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
