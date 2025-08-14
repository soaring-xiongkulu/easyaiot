import unittest
from app import app

class AppTestCase(unittest.TestCase):
    def setUp(self):
        # 修复Werkzeug版本访问问题
        import werkzeug
        if not hasattr(werkzeug, '__version__'):
            werkzeug.__version__ = '2.0.0'  # 设置默认版本
        self.app = app.test_client()
        self.app.testing = True

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "欢迎访问EasyAIoT平台")

    def test_health_check(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('healthy', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()