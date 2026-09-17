import unittest

from flask import Flask

from app.services.llm_template_seed import LLM_PRESET_MODELS, ensure_llm_template_seed
from db_models import LLMModel, db


class LlmTemplateSeedTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite://',
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    @staticmethod
    def _existing_model(name='QwenVL3视觉模型'):
        return LLMModel(
            name=name,
            service_type='online',
            vendor='aliyun',
            model_type='vision',
            model_name='qwen-vl-max',
            base_url='https://example.invalid/v1',
            api_key='real-user-key',
        )

    def test_adds_missing_presets_when_user_model_already_exists(self):
        with self.app.app_context():
            db.session.add(self._existing_model())
            db.session.commit()

            result = ensure_llm_template_seed()

            self.assertEqual(result, {'inserted': len(LLM_PRESET_MODELS), 'skipped': 0})
            self.assertEqual(LLMModel.query.count(), len(LLM_PRESET_MODELS) + 1)
            existing = LLMModel.query.filter_by(name='QwenVL3视觉模型').one()
            self.assertEqual(existing.api_key, 'real-user-key')

    def test_repeated_seed_is_idempotent(self):
        with self.app.app_context():
            first = ensure_llm_template_seed()
            second = ensure_llm_template_seed()

            self.assertEqual(first['inserted'], len(LLM_PRESET_MODELS))
            self.assertEqual(second, {'inserted': 0, 'skipped': len(LLM_PRESET_MODELS)})
            self.assertEqual(LLMModel.query.count(), len(LLM_PRESET_MODELS))

    def test_does_not_overwrite_same_named_user_configuration(self):
        preset_name = LLM_PRESET_MODELS[0]['name']
        with self.app.app_context():
            db.session.add(self._existing_model(name=preset_name))
            db.session.commit()

            result = ensure_llm_template_seed()

            self.assertEqual(result['inserted'], len(LLM_PRESET_MODELS) - 1)
            self.assertEqual(result['skipped'], 1)
            existing = LLMModel.query.filter_by(name=preset_name).one()
            self.assertEqual(existing.api_key, 'real-user-key')


if __name__ == '__main__':
    unittest.main()
