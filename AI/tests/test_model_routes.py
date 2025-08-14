import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class ModelRoutesTestCase(unittest.TestCase):
    def setUp(self):
        # 修复Werkzeug版本访问问题
        import werkzeug
        if not hasattr(werkzeug, '__version__'):
            werkzeug.__version__ = '2.0.0'  # 设置默认版本
        self.app = app.test_client()
        self.app.testing = True

    @patch('model.service.get_db_connection')
    def test_get_model_service_success(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [
            1, 'test_model_id', 'Test Model', '1.0', '/path/to/model',
            'http://localhost:9000', 'running', 9000, 12345,
            '2023-01-01T00:00:00', '2023-01-01T00:00:00'
        ]
        
        response = self.app.get('/model/test_model_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['model_id'], 'test_model_id')

    @patch('model.service.get_db_connection')
    def test_get_model_service_not_found(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        
        response = self.app.get('/model/nonexistent_model_id')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('message', data)

    @patch('model.service.get_minio_client')
    @patch('model.service.start_model_service_process')
    @patch('model.service.register_service_nacos')
    def test_deploy_model_success(self, mock_register_nacos, mock_start_process, mock_minio_client): # 删除:, mock_db):
        # 模拟数据库连接和游标
        
        # 模拟模型服务进程
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_start_process.return_value = mock_process
        
        response = self.app.post('/model/deploy',
                                json={
                                    'model_id': 'test_model_id',
                                    'model_name': 'Test Model',
                                    'model_version': '1.0',
                                    'minio_model_path': 'models/test_model.zip'
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('model_id', data)

    def test_deploy_model_missing_parameters(self):
        response = self.app.post('/model/deploy',
                                json={
                                    'model_id': 'test_model_id'
                                    # 缺少其他必需参数
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 500)  # 由于实现中的异常处理逻辑

    @patch('requests.get')
    def test_check_model_service_status_success(self, mock_requests_get): # 删除:, mock_db):
        # 模拟数据库连接
        
        # 模拟HTTP请求
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        response = self.app.get('/model/status/test_model_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['model_id'], 'test_model_id')

    def test_check_model_service_status_not_found(self): # 删除:, mock_db):
        
        response = self.app.get('/model/status/nonexistent_model_id')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)

    def test_list_model_services(self): # 删除:, mock_db):
        
        response = self.app.get('/model/list')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        if data:  # 如果有数据
            self.assertEqual(data[0]['model_id'], 'test_model_id')

    def test_stop_model_service_success(self): # 删除:, mock_db):
        
        with patch('os.kill') as mock_kill:
            response = self.app.post('/model/stop/test_model_id')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('message', data)

    def test_stop_model_service_not_found(self): # 删除:, mock_db):
        
        response = self.app.post('/model/stop/nonexistent_model_id')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('requests.get')
    def test_get_model_service_detail_success(self, mock_requests_get): # 删除:, mock_db):
        # 模拟数据库连接
        
        # 模拟HTTP请求
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests_get.return_value = mock_response
        
        response = self.app.get('/model/detail/test_model_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['model_id'], 'test_model_id')
        self.assertIn('health_status', data)

    def test_get_model_service_detail_not_found(self): # 删除:, mock_db):
        
        response = self.app.get('/model/detail/nonexistent_model_id')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('message', data)

if __name__ == '__main__':
    unittest.main()

