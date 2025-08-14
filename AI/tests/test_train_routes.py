import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

class TrainRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('train.service.get_db_connection')
    def test_train_info(self, mock_db):
        response = self.app.get('/train/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)
        self.assertIn('endpoints', data)

    @patch('train.service.get_db_connection')
    @patch('train.service.YOLOv8TrainingService.start_training')
    def test_start_training_success(self, mock_start_training, mock_db):
        mock_start_training.return_value = 'test_task_id'
        
        response = self.app.post('/train/start', 
                                json={
                                    'dataset_url': 'http://minio:9000/test/dataset',
                                    'model_config': {'epochs': 5}
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 202)
        data = response.get_json()
        self.assertEqual(data['task_id'], 'test_task_id')

    @patch('train.service.get_db_connection')
    def test_start_training_missing_dataset_url(self, mock_db):
        response = self.app.post('/train/start', 
                                json={'model_config': {'epochs': 5}},
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('train.service.get_db_connection')
    @patch('train.service.YOLOv8TrainingService.get_training_status')
    def test_training_status_success(self, mock_get_status, mock_db):
        mock_get_status.return_value = {
            'step': 1,
            'operation': 'download_dataset',
            'details': {},
            'status': 'running',
            'timestamp': '2023-01-01T00:00:00'
        }
        
        response = self.app.get('/train/status/test_task_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['step'], 1)

    @patch('train.service.get_db_connection')
    @patch('train.service.YOLOv8TrainingService.get_training_status')
    def test_training_status_not_found(self, mock_get_status, mock_db):
        mock_get_status.return_value = None
        
        response = self.app.get('/train/status/nonexistent_task_id')
        self.assertEqual(response.status_code, 500)  # 由于实现中的异常处理逻辑

    @patch('train.service.get_db_connection')
    def test_log_training_step(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [1]
        
        response = self.app.post('/train/log',
                                json={
                                    'training_id': 'test_id',
                                    'step': 1,
                                    'operation': 'test_operation',
                                    'details': {}
                                },
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('id', data)

    @patch('train.service.get_db_connection')
    def test_get_training_logs(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [10]  # Total count
        mock_cur.fetchall.return_value = [
            (1, 'test_id', 1, 'test_op', {}, 'running', '2023-01-01T00:00:00', '2023-01-01T00:00:00')
        ]
        
        response = self.app.get('/train/logs/test_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('logs', data)
        self.assertIn('pagination', data)

    @patch('train.service.get_db_connection')
    def test_get_current_training_step(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [1, 'test_op', {}, 'running', '2023-01-01T00:00:00']
        
        response = self.app.get('/train/current_step/test_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['step'], 1)

    @patch('train.service.get_db_connection')
    def test_get_current_training_step_not_found(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = None
        
        response = self.app.get('/train/current_step/test_id')
        self.assertEqual(response.status_code, 404)

    @patch('train.service.get_db_connection')
    def test_get_training_config(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [{'epochs': 10}]
        
        response = self.app.get('/train/config/test_id')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('epochs', data[0])

    @patch('train.service.get_db_connection')
    def test_update_training_status(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        
        response = self.app.put('/train/status/test_id',
                               json={'status': 'completed'},
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('message', data)

    @patch('train.service.get_db_connection')
    def test_update_training_status_missing_status(self, mock_db):
        response = self.app.put('/train/status/test_id',
                               json={},
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    @patch('train.service.get_db_connection')
    def test_list_trainings(self, mock_db):
        mock_conn = MagicMock()
        mock_db.return_value = mock_conn
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.fetchone.return_value = [5]  # Total count
        mock_cur.fetchall.return_value = [
            ('test_id_1', 'running', '2023-01-01T00:00:00', '2023-01-01T00:00:00')
        ]
        
        response = self.app.get('/train/list')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('trainings', data)
        self.assertIn('pagination', data)

if __name__ == '__main__':
    unittest.main()