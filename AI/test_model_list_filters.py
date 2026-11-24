import unittest

from flask import Flask

from app.blueprints.model import model_bp, models
from db_models import Model, db


class ModelListFilterTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        self.app.register_blueprint(model_bp, url_prefix='/model')
        with self.app.app_context():
            db.create_all()
            db.session.add_all([
                Model(name='crowd-detector', version='1.0.0', model_path='/models/crowd.pt'),
                Model(name='crowd-counter', version='1.0.7', onnx_model_path='/models/counter.onnx'),
                Model(name='rknn-detector', version='1.0.0', rknn_model_path='/models/rknn.rknn'),
                Model(name='vehicle-detector', version='1.0.7'),
            ])
            db.session.commit()
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _get_payload(self, query_string):
        with self.app.test_request_context(f'/model/list?{query_string}'):
            return models().get_json()

    def test_filters_by_model_name(self):
        payload = self._get_payload('name=crowd')

        self.assertEqual(payload['total'], 2)

    def test_filters_by_normalized_model_version(self):
        payload = self._get_payload('version=v1.0.7')

        self.assertEqual(payload['total'], 2)

    def test_combines_name_and_version_filters(self):
        payload = self._get_payload('name=crowd&version=1.0.7')

        self.assertEqual(payload['total'], 1)
        self.assertEqual(payload['data'][0]['name'], 'crowd-counter')

    def test_filters_models_with_any_available_weights(self):
        payload = self._get_payload('has_weights=true')

        self.assertEqual(payload['total'], 3)
        self.assertEqual(
            {row['name'] for row in payload['data']},
            {'crowd-detector', 'crowd-counter', 'rknn-detector'},
        )


if __name__ == '__main__':
    unittest.main()
