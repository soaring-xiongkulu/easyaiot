import unittest
from unittest.mock import MagicMock, patch

from flask import has_app_context

from app.services import auto_label_dataset_writer
from app.services.auto_label_orchestrator import _yolo_to_annotations
from services.auto_label_worker import run_worker


class FakeResponse:
    status_code = 200

    def json(self):
        return {'code': 0, 'data': {'list': [{'id': 1}]}}


class PageResponse:
    status_code = 200

    def __init__(self, rows):
        self.rows = rows

    def json(self):
        return {'code': 0, 'data': {'list': self.rows}}


class WriteResponse:
    status_code = 200

    def json(self):
        return {'code': 0}


class AutoLabelWorkerTest(unittest.TestCase):
    def test_initial_counters_are_loaded_from_dispatch_environment(self):
        with patch.dict(
            run_worker.os.environ,
            {
                'INITIAL_CAPTURED_COUNT': '6',
                'INITIAL_LABELED_COUNT': '27',
                'INITIAL_FAILED_COUNT': '2',
            },
        ):
            counters = run_worker._initial_counters()

        self.assertEqual(counters, (6, 27, 2))

    def test_fetch_unlabeled_uses_integer_completed_filter(self):
        with patch.object(run_worker.requests, 'get', return_value=FakeResponse()) as request_get:
            images = run_worker._fetch_unlabeled('http://gateway.test', 5)

        self.assertEqual(images, [{'id': 1}])
        completed = request_get.call_args.kwargs['params']['completed']
        self.assertIs(type(completed), int)
        self.assertEqual(completed, 0)

    def test_fetch_unlabeled_pages_past_images_already_attempted_by_task(self):
        def get_page(*_args, **kwargs):
            page_no = kwargs['params']['pageNo']
            rows = {
                1: [{'id': 1}, {'id': 2}],
                2: [{'id': 3}],
            }.get(page_no, [])
            return PageResponse(rows)

        with patch.object(run_worker.requests, 'get', side_effect=get_page):
            images = run_worker._fetch_unlabeled(
                'http://gateway.test',
                5,
                limit=2,
                exclude_ids={1, 2},
            )

        self.assertEqual(images, [{'id': 3}])

    def test_parent_task_url_matches_blueprint_prefix(self):
        self.assertEqual(
            run_worker._parent_task_url('http://ai.test/', 5, 13),
            'http://ai.test/model/dataset/dataset/5/auto-label/task/13',
        )

    def test_label_batch_runs_inside_worker_application_context(self):
        context_state = []

        def label_batch_impl(*_args, **_kwargs):
            context_state.append(has_app_context())
            return 1, 0

        with patch.object(run_worker, '_label_batch_impl', side_effect=label_batch_impl):
            result = run_worker._label_batch(object(), [], 'http://gateway.test', 5)

        self.assertEqual(result, (1, 0))
        self.assertEqual(context_state, [True])

    def test_yolo_rectangle_uses_four_canvas_corners(self):
        annotations = _yolo_to_annotations(
            [
                {
                    'bbox': [64, 48, 320, 240],
                    'class_name': 'object',
                    'confidence': 0.9,
                },
            ],
            image_width=640,
            image_height=480,
        )

        self.assertEqual(
            annotations[0]['points'],
            [
                {'x': 0.1, 'y': 0.1},
                {'x': 0.5, 'y': 0.1},
                {'x': 0.5, 'y': 0.5},
                {'x': 0.1, 'y': 0.5},
            ],
        )

    def test_dataset_writer_deletes_empty_image_when_filter_enabled(self):
        with patch.object(
            auto_label_dataset_writer.requests,
            'delete',
            return_value=WriteResponse(),
        ) as request_delete, patch.object(
            auto_label_dataset_writer.requests,
            'put',
        ) as request_put:
            result = auto_label_dataset_writer.write_auto_label_result(
                'http://gateway.test',
                5,
                7,
                [],
                keep_annotated_images_only=True,
            )

        self.assertEqual(result, ('[]', 'deleted'))
        request_delete.assert_called_once_with(
            'http://gateway.test/admin-api/dataset/image/delete/7',
            timeout=15,
        )
        request_put.assert_not_called()

    def test_dataset_writer_keeps_empty_image_pending_when_filter_disabled(self):
        with patch.object(
            auto_label_dataset_writer.requests,
            'delete',
        ) as request_delete, patch.object(
            auto_label_dataset_writer.requests,
            'put',
            return_value=WriteResponse(),
        ) as request_put:
            result = auto_label_dataset_writer.write_auto_label_result(
                'http://gateway.test',
                5,
                7,
                [],
                keep_annotated_images_only=False,
            )

        self.assertEqual(result, ('[]', 'updated'))
        request_delete.assert_not_called()
        self.assertEqual(request_put.call_args.kwargs['json']['completed'], 0)

    def test_successful_empty_inference_is_deleted_by_default(self):
        image_open = MagicMock()
        image_open.__enter__.return_value.size = (640, 480)
        attempted_image_ids = set()
        task_proxy = MagicMock()
        task_proxy.id = 13

        with patch.dict(
            run_worker.os.environ,
            {'KEEP_ANNOTATED_IMAGES_ONLY': 'true'},
        ), patch(
            'app.services.minio_service.ModelService.download_from_minio',
            return_value=(True, None),
        ), patch(
            'app.services.sam_service.get_sam_service',
            return_value=object(),
        ), patch(
            'app.services.auto_label_orchestrator.label_image_with_strategy',
            return_value=([], 'yolo'),
        ), patch(
            'app.services.auto_label_orchestrator._update_counters',
        ), patch.object(
            run_worker,
            '_record_auto_label_result',
        ) as record_result, patch(
            'PIL.Image.open',
            return_value=image_open,
        ), patch(
            'app.services.auto_label_dataset_writer.write_auto_label_result',
            return_value=('[]', 'deleted'),
        ) as write_result:
            result = run_worker._label_batch_impl(
                task_proxy,
                [
                    {
                        'id': 7,
                        'path': 'http://minio.test/minio/browser/buckets/dataset?prefix=empty.jpg',
                    },
                ],
                'http://gateway.test',
                5,
                attempted_image_ids,
            )

        self.assertEqual(result, (0, 0))
        write_result.assert_called_once_with(
            'http://gateway.test',
            5,
            7,
            [],
            keep_annotated_images_only=True,
        )
        record_result.assert_called_once_with(13, 7, '[]')
        self.assertEqual(attempted_image_ids, {7})

    def test_successful_empty_inference_leaves_image_pending_when_filter_disabled(self):
        image_open = MagicMock()
        image_open.__enter__.return_value.size = (640, 480)
        attempted_image_ids = set()
        task_proxy = MagicMock()
        task_proxy.id = 13

        with patch.dict(
            run_worker.os.environ,
            {'KEEP_ANNOTATED_IMAGES_ONLY': 'false'},
        ), patch(
            'app.services.minio_service.ModelService.download_from_minio',
            return_value=(True, None),
        ), patch(
            'app.services.sam_service.get_sam_service',
            return_value=object(),
        ), patch(
            'app.services.auto_label_orchestrator.label_image_with_strategy',
            return_value=([], 'yolo'),
        ), patch(
            'app.services.auto_label_orchestrator._update_counters',
        ), patch.object(
            run_worker,
            '_record_auto_label_result',
        ) as record_result, patch(
            'PIL.Image.open',
            return_value=image_open,
        ), patch(
            'app.services.auto_label_dataset_writer.write_auto_label_result',
            return_value=('[]', 'updated'),
        ) as write_result:
            result = run_worker._label_batch_impl(
                task_proxy,
                [
                    {
                        'id': 7,
                        'path': 'http://minio.test/minio/browser/buckets/dataset?prefix=empty.jpg',
                    },
                ],
                'http://gateway.test',
                5,
                attempted_image_ids,
            )

        self.assertEqual(result, (0, 0))
        write_result.assert_called_once_with(
            'http://gateway.test',
            5,
            7,
            [],
            keep_annotated_images_only=False,
        )
        record_result.assert_called_once_with(13, 7, '[]')
        self.assertEqual(attempted_image_ids, {7})


if __name__ == '__main__':
    unittest.main()
