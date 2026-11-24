"""RKNN 模型上传与登记回归测试。"""
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

from app.blueprints.model import ModelService, model_bp
from app.utils.rknn_validator import validate_rknn_model
from db_models import Model, db


class RknnValidatorTest(unittest.TestCase):
    def _write_rknn(self, content: bytes) -> str:
        handle = tempfile.NamedTemporaryFile(delete=False, suffix='.rknn')
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_accepts_current_and_legacy_magic(self):
        current = self._write_rknn(b'RKNN' + b'\x00' * 64)
        legacy = self._write_rknn(b'RKN1' + b'\x00' * 64)

        self.assertEqual(validate_rknn_model(current)['magic'], 'RKNN')
        self.assertEqual(validate_rknn_model(legacy)['magic'], 'RKN1')

    def test_rejects_invalid_magic(self):
        path = self._write_rknn(b'ONNX' + b'\x00' * 64)

        with self.assertRaisesRegex(ValueError, 'RKNN/RKN1'):
            validate_rknn_model(path)

    def test_rejects_too_small_file(self):
        path = self._write_rknn(b'RKNN')

        with self.assertRaisesRegex(ValueError, '过小'):
            validate_rknn_model(path)


class RknnModelUploadTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(model_bp, url_prefix='/model')
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def _upload(self, content: bytes, filename: str, **form):
        data = {
            'file': (io.BytesIO(content), filename),
            'save_to_db': 'true',
            **form,
        }
        return self.client.post(
            '/model/upload',
            data=data,
            content_type='multipart/form-data',
        )

    def test_upload_rknn_saves_to_dedicated_column(self):
        with patch.object(ModelService, 'upload_to_minio', return_value=(True, '')), \
                patch('app.blueprints.model.download_default_model_image', return_value=False):
            response = self._upload(
                b'RKNN' + b'\x00' * 64,
                'yolov8n-rk3588.rknn',
                name='rknn-detector',
                classNames='["person","car"]',
            )

        payload = response.get_json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['model_format'], 'rknn')
        self.assertEqual(payload['data']['class_names'], ['person', 'car'])

        with self.app.app_context():
            model = Model.query.filter_by(name='rknn-detector').one()
            self.assertEqual(model.rknn_model_path, payload['data']['url'])
            self.assertIsNone(model.model_path)
            self.assertIsNone(model.onnx_model_path)

    def test_upload_rejects_fake_rknn_file(self):
        with patch.object(ModelService, 'upload_to_minio', return_value=(True, '')):
            response = self._upload(b'ONNX' + b'\x00' * 64, 'fake.rknn')

        self.assertEqual(response.status_code, 400)
        self.assertIn('RKNN/RKN1', response.get_json()['msg'])
        with self.app.app_context():
            self.assertEqual(Model.query.count(), 0)

    def test_create_model_registers_rknn_path(self):
        # 前端上传接口返回的是 MinIO 下载 URL，扩展名藏在 prefix 查询参数中
        rknn_url = '/api/v1/buckets/models/objects/download?prefix=rknn/created.rknn'
        response = self.client.post('/model/create', json={
            'name': 'rknn-created',
            'version': '1.0.0',
            'filePath': rknn_url,
            'classNames': ['person'],
        })

        payload = response.get_json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['filePath'], rknn_url)
        with self.app.app_context():
            model = Model.query.filter_by(name='rknn-created').one()
            self.assertEqual(model.rknn_model_path, rknn_url)
            self.assertIsNone(model.model_path)

    def test_create_model_keeps_pt_in_model_path(self):
        pt_url = '/api/v1/buckets/models/objects/download?prefix=yolo/yolov8/best.pt'
        response = self.client.post('/model/create', json={
            'name': 'pt-created',
            'version': '1.0.0',
            'filePath': pt_url,
        })

        payload = response.get_json()
        self.assertEqual(payload['code'], 0)
        with self.app.app_context():
            model = Model.query.filter_by(name='pt-created').one()
            self.assertEqual(model.model_path, pt_url)
            self.assertIsNone(model.rknn_model_path)

    def test_download_rknn_uses_rknn_filename(self):
        rknn_url = '/api/v1/buckets/models/objects/download?prefix=rknn/download.rknn'
        with self.app.app_context():
            model = Model(name='rknn-download', version='2.0.0', rknn_model_path=rknn_url)
            db.session.add(model)
            db.session.commit()
            model_id = model.id

        def fake_download(bucket_name, object_key, target_path):
            with open(target_path, 'wb') as file_obj:
                file_obj.write(b'RKNN' + b'\x00' * 64)
            return True, ''

        with patch.object(ModelService, 'download_from_minio', side_effect=fake_download):
            response = self.client.get(f'/model/{model_id}/download')

        self.assertEqual(response.status_code, 200)
        disposition = response.headers.get('Content-Disposition', '')
        self.assertIn('.rknn', disposition)

    def test_update_model_registers_rknn_path(self):
        rknn_url = '/api/v1/buckets/models/objects/download?prefix=rknn/updated.rknn'
        with self.app.app_context():
            model = Model(name='rknn-updated', version='1.0.0')
            db.session.add(model)
            db.session.commit()
            model_id = model.id

        response = self.client.put(f'/model/{model_id}/update', json={
            'filePath': rknn_url,
        })

        payload = response.get_json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['filePath'], rknn_url)
        self.assertEqual(payload['data']['rknn_model_path'], rknn_url)
        with self.app.app_context():
            model = db.session.get(Model, model_id)
            self.assertEqual(model.rknn_model_path, rknn_url)
            self.assertIsNone(model.model_path)


if __name__ == '__main__':
    unittest.main()
