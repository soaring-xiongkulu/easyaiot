"""任务/模型级区域服务的确定性单元测试。

这些测试不依赖线上数据库，重点锁定批量事务、乐观锁、任务隔离和输入校验。
"""
import json
import math
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services import device_detection_region_service as service


SQUARE = [
    {'x': 0.1, 'y': 0.1},
    {'x': 0.9, 'y': 0.1},
    {'x': 0.9, 'y': 0.9},
    {'x': 0.1, 'y': 0.9},
]


def region_payload(**overrides):
    payload = {
        'region_name': '测试区域',
        'region_type': 'polygon',
        'points': SQUARE,
        'model_scope': 'all',
        'model_ids': [],
        'opacity': 0.3,
        'sort_order': 0,
        'hit_mode': 'center',
        'min_overlap_ratio': 0.5,
    }
    payload.update(overrides)
    return payload


class RegionValidationTest(unittest.TestCase):
    def setUp(self):
        self.task = SimpleNamespace(id=7, model_ids='[11, 12, -1]')

    def test_model_ids_are_deduplicated_sorted_and_invalid_input_is_empty(self):
        self.assertEqual([-1, 11, 12], service._parse_model_ids('[12, 11, 12, -1]'))
        self.assertEqual([], service._parse_model_ids('{bad json'))

    def test_all_model_scope_persists_as_null(self):
        normalized = service._normalize_region_payload(region_payload(), self.task)
        self.assertIsNone(normalized['model_ids'])

    def test_selected_models_are_deduplicated_and_sorted(self):
        normalized = service._normalize_region_payload(
            region_payload(model_scope='selected', model_ids=[12, 11, 12]), self.task
        )
        self.assertEqual([11, 12], json.loads(normalized['model_ids']))

    def test_selected_scope_rejects_empty_foreign_and_reserved_zero_models(self):
        cases = [
            region_payload(model_scope='selected', model_ids=[]),
            region_payload(model_scope='selected', model_ids=[999]),
            region_payload(model_scope='selected', model_ids=[0]),
        ]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                service._normalize_region_payload(payload, self.task)

    def test_region_type_and_name_are_required(self):
        for payload in (
            region_payload(region_type='circle'),
            region_payload(region_name='   '),
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                service._normalize_region_payload(payload, self.task)

    def test_polygon_rectangle_and_line_point_counts(self):
        invalid = [
            ('polygon', SQUARE[:2]),
            ('rectangle', SQUARE[:3]),
            ('line', SQUARE[:1]),
            ('line', SQUARE[:3]),
        ]
        for region_type, points in invalid:
            with self.subTest(region_type=region_type), self.assertRaises(ValueError):
                service._validate_points(region_type, points)

        self.assertEqual(4, len(service._validate_points('rectangle', SQUARE)))
        self.assertEqual(2, len(service._validate_points('line', SQUARE[:2])))

    def test_points_reject_bad_shape_non_numeric_non_finite_and_out_of_range(self):
        invalid_points = [
            'not-a-list',
            [{'x': 0.1}] * 3,
            [{'x': 'bad', 'y': 0.1}] * 3,
            [{'x': math.nan, 'y': 0.1}, *SQUARE[1:]],
            [{'x': math.inf, 'y': 0.1}, *SQUARE[1:]],
            [{'x': 1.01, 'y': 0.1}, *SQUARE[1:]],
            [{'x': -0.01, 'y': 0.1}, *SQUARE[1:]],
        ]
        for points in invalid_points:
            with self.subTest(points=points), self.assertRaises(ValueError):
                service._validate_points('polygon', points)

    def test_polygon_rejects_zero_area_self_intersection_and_more_than_64_points(self):
        zero_area = [{'x': 0.1, 'y': 0.1}, {'x': 0.2, 'y': 0.2}, {'x': 0.3, 'y': 0.3}]
        bow_tie = [
            {'x': 0.1, 'y': 0.1}, {'x': 0.9, 'y': 0.9},
            {'x': 0.1, 'y': 0.9}, {'x': 0.9, 'y': 0.1},
        ]
        too_many = [
            {'x': 0.5 + 0.4 * math.cos(i * 2 * math.pi / 65),
             'y': 0.5 + 0.4 * math.sin(i * 2 * math.pi / 65)}
            for i in range(65)
        ]
        for points in (zero_area, bow_tie, too_many):
            with self.subTest(size=len(points)), self.assertRaises(ValueError):
                service._validate_points('polygon', points)

    def test_opacity_and_sort_order_bounds(self):
        for payload in (
            region_payload(opacity=-0.1),
            region_payload(opacity=1.1),
            region_payload(opacity='bad'),
            region_payload(sort_order=-1),
            region_payload(sort_order='bad'),
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                service._normalize_region_payload(payload, self.task)

    def test_region_level_hit_mode_and_overlap_ratio_are_validated(self):
        normalized = service._normalize_region_payload(
            region_payload(hit_mode='overlap_ratio', min_overlap_ratio=0.65), self.task
        )
        self.assertEqual('overlap_ratio', normalized['hit_mode'])
        self.assertEqual(0.65, normalized['min_overlap_ratio'])

        for payload in (
            region_payload(hit_mode='unknown'),
            region_payload(hit_mode='overlap_ratio', min_overlap_ratio=0),
            region_payload(hit_mode='overlap_ratio', min_overlap_ratio=1.01),
            region_payload(hit_mode='overlap_ratio', min_overlap_ratio='0.5'),
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                service._normalize_region_payload(payload, self.task)

    def test_reference_image_must_exist_and_belong_to_device(self):
        query = MagicMock()
        with patch.object(service, 'Image', SimpleNamespace(query=query)):
            query.get.return_value = None
            with self.assertRaisesRegex(ValueError, '图片不存在'):
                service._normalize_region_payload(
                    region_payload(image_id=5, device_id='cam-a'), self.task
                )

            query.get.return_value = SimpleNamespace(id=5, device_id='cam-b')
            with self.assertRaisesRegex(ValueError, '参考图片不属于当前设备'):
                service._normalize_region_payload(
                    region_payload(image_id=5, device_id='cam-a'), self.task
                )


class ReplaceRegionsTransactionTest(unittest.TestCase):
    def setUp(self):
        self.task = SimpleNamespace(id=7, model_ids='[11, 12]', template_revision=4)
        self.session = MagicMock()
        self.task_query = MagicMock()
        self.task_query.filter_by.return_value.with_for_update.return_value.first.return_value = self.task
        self.existing_query = MagicMock()
        self.region_model = MagicMock()
        self.region_model.query = self.existing_query

        self.patches = [
            patch.object(service, 'AlgorithmTask', SimpleNamespace(query=self.task_query)),
            patch.object(service, 'DeviceDetectionRegion', self.region_model),
            patch.object(service.db, 'session', self.session),
            patch.object(service, '_validate_task_device', return_value=self.task),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def set_existing(self, rows):
        self.existing_query.filter_by.return_value.all.return_value = rows

    def test_batch_create_update_delete_commits_once_and_bumps_revision_once(self):
        keep = SimpleNamespace(id=1, region_name='旧名称')
        remove = SimpleNamespace(id=2, region_name='待删除')
        created = SimpleNamespace(id=None)
        self.set_existing([keep, remove])
        self.region_model.return_value = created

        saved, revision = service.replace_device_regions(
            'cam-a', 7,
            [region_payload(id=1, region_name='新名称'), region_payload(region_name='新增')],
            expected_revision=4,
        )

        self.assertEqual([keep, created], saved)
        self.assertEqual(5, revision)
        self.assertEqual(5, self.task.template_revision)
        self.session.commit.assert_called_once_with()
        self.session.delete.assert_called_once_with(remove)
        self.session.rollback.assert_not_called()
        self.assertEqual('新名称', keep.region_name)

    def test_invalid_item_rolls_back_entire_batch_without_revision_change(self):
        self.set_existing([])
        with self.assertRaises(ValueError):
            service.replace_device_regions(
                'cam-a', 7,
                [region_payload(), region_payload(region_name='坏区域', opacity=2)],
                expected_revision=4,
            )
        self.assertEqual(4, self.task.template_revision)
        self.session.commit.assert_not_called()
        self.session.rollback.assert_called_once_with()

    def test_stale_revision_rejected_before_any_write(self):
        self.set_existing([])
        with self.assertRaises(service.RegionRevisionConflict):
            service.replace_device_regions('cam-a', 7, [], expected_revision=3)
        self.session.commit.assert_not_called()
        self.session.rollback.assert_called_once_with()

    def test_duplicate_and_foreign_region_ids_are_rejected(self):
        existing = SimpleNamespace(id=1)
        self.set_existing([existing])
        cases = [
            [region_payload(id=1), region_payload(id=1, region_name='重复')],
            [region_payload(id=99)],
        ]
        for regions in cases:
            self.session.reset_mock()
            self.task.template_revision = 4
            with self.subTest(regions=regions), self.assertRaises(ValueError):
                service.replace_device_regions('cam-a', 7, regions, expected_revision=4)
            self.session.commit.assert_not_called()
            self.session.rollback.assert_called_once_with()

    def test_region_limit_accepts_100_and_rejects_101(self):
        self.set_existing([])
        regions = [region_payload(region_name=f'区域-{i}', sort_order=i) for i in range(100)]
        self.region_model.side_effect = lambda **kw: SimpleNamespace(**kw)
        _, revision = service.replace_device_regions('cam-a', 7, regions, expected_revision=4)
        self.assertEqual(5, revision)

        self.session.reset_mock()
        with self.assertRaisesRegex(ValueError, '最多支持100个区域'):
            service.replace_device_regions('cam-a', 7, regions + [region_payload()], expected_revision=5)
        self.session.commit.assert_not_called()
        self.session.rollback.assert_not_called()

    def test_task_without_real_models_is_rejected(self):
        self.task.model_ids = '[0]'
        self.set_existing([])
        with self.assertRaisesRegex(ValueError, '未配置算法模型列表'):
            service.replace_device_regions('cam-a', 7, [], expected_revision=4)
        self.session.rollback.assert_called_once_with()


class TaskDeviceIsolationTest(unittest.TestCase):
    def test_device_must_exist_and_belong_to_task(self):
        task = SimpleNamespace(id=7, devices=[SimpleNamespace(id='cam-a')])
        task_query = MagicMock()
        device_query = MagicMock()
        with patch.object(service, 'AlgorithmTask', SimpleNamespace(query=task_query)), \
                patch.object(service, 'Device', SimpleNamespace(query=device_query)):
            task_query.get.return_value = task
            device_query.get.return_value = None
            with self.assertRaisesRegex(ValueError, '设备不存在'):
                service._validate_task_device(7, 'cam-b')

            device_query.get.return_value = SimpleNamespace(id='cam-b')
            with self.assertRaisesRegex(ValueError, '不属于算法任务'):
                service._validate_task_device(7, 'cam-b')

            device_query.get.return_value = SimpleNamespace(id='cam-a')
            self.assertIs(task, service._validate_task_device(7, 'cam-a'))


if __name__ == '__main__':
    unittest.main()
