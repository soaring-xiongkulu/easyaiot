import json
from utils.database import get_db_connection
# 添加YOLOv8TrainingService类的实现
from ultralytics import YOLO
import uuid
import os
from utils.minio_client import download_from_minio
import threading
import time
# 添加MinIO客户端相关导入
from utils.minio_client import get_minio_client
from urllib.parse import urlparse
# 添加线程池相关导入
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

class YOLOv8TrainingService:
    def __init__(self, max_workers=3):
        # 使用线程池管理训练任务
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.training_tasks = {}
        self.task_futures = {}
    
    def start_training(self, dataset_url, model_config):
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 提交训练任务到线程池
        future = self.executor.submit(self._run_training, task_id, dataset_url, model_config)
        
        # 记录训练任务和对应的future
        self.task_futures[task_id] = future
        self.training_tasks[task_id] = {
            'status': 'started',
            'dataset_url': dataset_url,
            'model_config': model_config
        }
        
        # 添加future完成回调
        future.add_done_callback(lambda f: self._training_completed(task_id, f))
        
        return task_id
    
    def _training_completed(self, task_id, future):
        # 当训练任务完成时更新状态
        try:
            result = future.result()
            self.training_tasks[task_id]['status'] = 'completed'
        except Exception as e:
            self.training_tasks[task_id]['status'] = 'failed'
            self._log_training_step(task_id, -1, 'training_error', {
                'error': str(e)
            }, 'failed', f'训练出错: {str(e)}')
    
    def _run_training(self, task_id, dataset_url, model_config):
        try:
            # 记录训练开始
            self._log_training_step(task_id, 0, 'training_start', {
                'dataset_url': dataset_url,
                'model_config': model_config
            }, 'running', '开始训练任务')
            
            # 下载数据集
            self._log_training_step(task_id, 1, 'download_dataset', {
                'url': dataset_url
            }, 'running', '正在下载数据集')
            
            # 实现实际的数据集下载逻辑
            dataset_path = self._download_dataset(dataset_url, task_id)
            
            # 配置模型
            self._log_training_step(task_id, 2, 'configure_model', {
                'config': model_config
            }, 'running', '正在配置模型')
            
            # 加载模型
            model_type = model_config.get('model_type', 'yolov8n.pt')
            model = YOLO(model_type)
            
            # 设置训练参数
            epochs = model_config.get('epochs', 10)
            imgsz = model_config.get('imgsz', 640)
            batch_size = model_config.get('batch_size', 16)
            
            # 开始训练
            self._log_training_step(task_id, 3, 'training_started', {
                'epochs': epochs,
                'imgsz': imgsz,
                'batch_size': batch_size
            }, 'running', f'开始训练，共 {epochs} 轮，图像尺寸 {imgsz}，批大小 {batch_size}')
            
            # 执行训练
            # 添加训练过程中的详细日志记录
            training_results = []
            
            def on_train_epoch_end(trainer):
                epoch = trainer.epoch
                metrics = trainer.metrics
                self._log_training_step(task_id, 3, 'training_epoch_end', {
                    'epoch': epoch,
                    'metrics': {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}
                }, 'running', f'训练轮次 {epoch+1} 完成')
                
            def on_train_batch_end(trainer):
                batch = trainer.batch
                if batch % 10 == 0:  # 每10个batch记录一次日志
                    self._log_training_step(task_id, 3, 'training_batch_end', {
                        'batch': batch,
                        'epoch': trainer.epoch
                    }, 'running', f'训练批次 {batch} 完成，当前轮次 {trainer.epoch+1}')
            
            # 注册回调函数
            model.add_callback('on_train_epoch_end', on_train_epoch_end)
            model.add_callback('on_train_batch_end', on_train_batch_end)
            
            results = model.train(
                data=dataset_path,
                epochs=epochs,
                imgsz=imgsz,
                batch=batch_size
            )
            
            # 保存模型
            model_save_path = f'/tmp/models/{task_id}.pt'
            model.save(model_save_path)
            
            # 训练完成
            self._log_training_step(task_id, 4, 'training_completed', {
                'model_path': model_save_path,
                'results': str(results)
            }, 'completed', f'训练完成，模型已保存至 {model_save_path}')
            
            # 自动保存最好的模型到数据库
            self._save_best_model_to_db(task_id, model_save_path, model_config)
            
        except Exception as e:
            # 记录错误
            self._log_training_step(task_id, -1, 'training_error', {
                'error': str(e)
            }, 'failed', f'训练出错: {str(e)}')
            raise e  # 重新抛出异常，以便ThreadPoolExecutor能捕获
    
    def _download_dataset(self, dataset_url, task_id):
        # 实现实际的数据集下载逻辑
        try:
            # 解析URL获取bucket和object名称
            parsed_url = urlparse(dataset_url)
            path_parts = parsed_url.path.lstrip('/').split('/', 1)
            if len(path_parts) != 2:
                raise ValueError("Invalid MinIO URL format")
            
            bucket_name = path_parts[0]
            folder_prefix = path_parts[1]
            
            # 创建本地存储路径
            local_dataset_path = f'/tmp/datasets/{uuid.uuid4()}'
            os.makedirs(local_dataset_path, exist_ok=True)
            
            # 创建MinIO客户端
            client = get_minio_client()
            
            # 检查存储桶是否存在，不存在则创建
            try:
                if not client.bucket_exists(bucket_name):
                    client.make_bucket(bucket_name)
            except Exception as e:
                print(f"存储桶创建失败: {e}")
                # 记录错误
                self._log_training_step(task_id, 1, 'download_dataset', {
                    'error': str(e)
                }, 'failed', f'存储桶创建失败: {str(e)}')
                # 出现异常时回退到默认数据集
                return 'coco128.yaml'
            
            # 列出文件夹中的所有对象
            objects = client.list_objects(bucket_name, prefix=folder_prefix, recursive=True)
            object_list = list(objects)
            
            # 记录总文件数
            total_files = len(object_list)
            self._log_training_step(task_id, 1, 'download_dataset', {
                'url': dataset_url,
                'total_files': total_files,
                'status': 'starting'
            }, 'running', f'开始下载数据集，共 {total_files} 个文件')
            
            # 下载每个对象
            for i, obj in enumerate(object_list):
                # 计算相对路径
                relative_path = obj.object_name[len(folder_prefix):].lstrip('/')
                if relative_path:  # 确保不是空路径
                    local_file_path = os.path.join(local_dataset_path, relative_path)
                    # 确保本地目录存在
                    local_dir = os.path.dirname(local_file_path)
                    os.makedirs(local_dir, exist_ok=True)
                    
                    # 下载文件
                    client.fget_object(bucket_name, obj.object_name, local_file_path)
                    
                    # 记录进度
                    progress = (i + 1) / total_files * 100
                    self._log_training_step(task_id, 1, 'download_dataset', {
                        'url': dataset_url,
                        'progress': f"{progress:.1f}%",
                        'downloaded': i + 1,
                        'total': total_files,
                        'current_file': relative_path
                    }, 'running', f'数据集下载进度: {progress:.1f}% ({i+1}/{total_files})，当前文件: {relative_path}')
            
            # 查找数据集配置文件 (通常是一个yaml文件)
            import glob
            yaml_files = glob.glob(os.path.join(local_dataset_path, '*.yaml'))
            if yaml_files:
                return yaml_files[0]  # 返回找到的第一个yaml文件路径
            else:
                # 如果没有找到yaml文件，返回默认数据集配置
                return 'coco128.yaml'
        except Exception as e:
            print(f"数据集下载失败: {e}")
            # 记录错误
            self._log_training_step(task_id, 1, 'download_dataset', {
                'error': str(e)
            }, 'failed', f'数据集下载失败: {str(e)}')
            # 出现异常时回退到默认数据集
            return 'coco128.yaml'
    
    def _log_training_step(self, training_id, step, operation, details, status, log_message=None):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO training_logs (training_id, step, operation, log_message, details, status) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;',
            (training_id, step, operation, log_message, json.dumps(details), status)
        )
        log_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return {"id": log_id, "message": "训练日志记录成功"}
    
    def get_training_status(self, task_id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''SELECT step, operation, details, status, created_at 
                      FROM training_logs 
                      WHERE training_id = %s 
                      ORDER BY step DESC, created_at DESC 
                      LIMIT 1;''', (task_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            current_step = {
                'step': result[0],
                'operation': result[1],
                'details': result[2],
                'status': result[3],
                'timestamp': result[4].isoformat() if result[4] else None
            }
            return current_step
        
        return None
    
    def _save_best_model_to_db(self, task_id, model_path, model_config):
        """
        将训练好的最佳模型保存到数据库和MinIO中
        """
        try:
            # 生成模型ID和相关信息
            model_id = f"model_{task_id}"
            model_name = model_config.get('model_name', f'Trained_Model_{task_id[:8]}')
            model_version = model_config.get('model_version', '1.0.0')
            
            # 记录模型保存步骤
            self._log_training_step(task_id, 5, 'saving_best_model', {
                'model_id': model_id,
                'model_name': model_name,
                'model_version': model_version
            }, 'running', '正在保存最佳模型')
            
            # 创建模型zip文件
            import zipfile
            import shutil
            import uuid
            
            # 创建临时目录
            temp_dir = f'/tmp/model_{uuid.uuid4()}'
            os.makedirs(temp_dir, exist_ok=True)
            
            # 复制模型文件到临时目录
            model_filename = f"{model_id}.pt"
            temp_model_path = os.path.join(temp_dir, model_filename)
            shutil.copy2(model_path, temp_model_path)
            
            # 创建模型配置文件
            config_data = {
                'model_id': model_id,
                'model_name': model_name,
                'model_version': model_version,
                'training_id': task_id,
                'created_at': time.time()
            }
            config_path = os.path.join(temp_dir, 'model_config.json')
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # 压缩为zip文件
            zip_filename = f"{model_id}_{model_version}.zip"
            zip_path = f'/tmp/{zip_filename}'
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                zipf.write(temp_model_path, model_filename)
                zipf.write(config_path, 'model_config.json')
            
            # 上传到MinIO
            minio_client = get_minio_client()
            minio_model_path = f"models/{model_id}/{zip_filename}"
            
            # 确保存储桶存在
            bucket_name = "ai-service-bucket"
            try:
                minio_client.make_bucket(bucket_name)
            except Exception:
                pass  # 存储桶可能已存在
            
            # 上传文件
            minio_client.fput_object(bucket_name, minio_model_path, zip_path)
            
            # 保存模型信息到existing_models表
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''INSERT INTO existing_models 
                         (model_id, model_name, model_version, model_description, model_path) 
                         VALUES (%s, %s, %s, %s, %s) RETURNING id;''',
                       (model_id, model_name, model_version, 
                        f"Auto-saved best model from training {task_id}", minio_model_path))
            model_db_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            # 清理临时文件
            shutil.rmtree(temp_dir)
            os.remove(zip_path)
            
            # 记录保存成功
            self._log_training_step(task_id, 5, 'model_saved', {
                'model_id': model_id,
                'model_db_id': model_db_id,
                'minio_path': minio_model_path
            }, 'completed', f'最佳模型已保存，模型ID: {model_id}')
            
        except Exception as e:
            error_msg = f"保存最佳模型失败: {str(e)}"
            self._log_training_step(task_id, 5, 'model_save_failed', {
                'error': str(e)
            }, 'failed', error_msg)

def log_training_step_service(training_id, step, operation, details, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO training_logs (training_id, step, operation, details, status) VALUES (%s, %s, %s, %s, %s) RETURNING id;',
        (training_id, step, operation, json.dumps(details), status)
    )
    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return {"id": log_id, "message": "Training log recorded successfully"}

def get_training_logs_service(training_id, page, per_page, offset):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 查询总数
    cur.execute('SELECT COUNT(*) FROM training_logs WHERE training_id = %s;', (training_id,))
    total = cur.fetchone()[0]
    
    # 查询日志记录
    cur.execute('''SELECT id, training_id, step, operation, details, status, created_at, updated_at 
                  FROM training_logs 
                  WHERE training_id = %s 
                  ORDER BY step ASC, created_at ASC 
                  LIMIT %s OFFSET %s;''', (training_id, per_page, offset))
    logs = cur.fetchall()
    cur.close()
    conn.close()
    
    logs_list = []
    for log in logs:
        logs_list.append({
            'id': log[0],
            'training_id': log[1],
            'step': log[2],
            'operation': log[3],
            'details': log[4],
            'status': log[5],
            'created_at': log[6].isoformat() if log[6] else None,
            'updated_at': log[7].isoformat() if log[7] else None
        })
    
    return {
        "logs": logs_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }

def get_current_training_step_service(training_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT step, operation, details, status, created_at 
                  FROM training_logs 
                  WHERE training_id = %s 
                  ORDER BY step DESC, created_at DESC 
                  LIMIT 1;''', (training_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        current_step = {
            'step': result[0],
            'operation': result[1],
            'details': result[2],
            'status': result[3],
            'timestamp': result[4].isoformat() if result[4] else None
        }
        return current_step
    
    return None

# 新增：获取训练配置
def get_training_config_service(training_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT model_config FROM training_logs 
                  WHERE training_id = %s AND operation = 'training_start'
                  ORDER BY created_at ASC LIMIT 1;''', (training_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result and result[0]:
        return result[0]
    return None

# 新增：更新训练状态
def update_training_status_service(training_id, status):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''UPDATE training_logs SET status = %s, updated_at = CURRENT_TIMESTAMP
                  WHERE training_id = %s;''', (status, training_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Training status updated successfully"}

# 新增：获取所有训练任务
def list_trainings_service(page, per_page, offset):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 查询总数
    cur.execute('SELECT COUNT(DISTINCT training_id) FROM training_logs;')
    total = cur.fetchone()[0]
    
    # 查询训练任务列表
    cur.execute('''SELECT DISTINCT training_id, status, created_at, updated_at
                  FROM training_logs 
                  ORDER BY created_at DESC 
                  LIMIT %s OFFSET %s;''', (per_page, offset))
    trainings = cur.fetchall()
    cur.close()
    conn.close()
    
    trainings_list = []
    for training in trainings:
        trainings_list.append({
            'training_id': training[0],
            'status': training[1],
            'created_at': training[2].isoformat() if training[2] else None,
            'updated_at': training[3].isoformat() if training[3] else None
        })
    
    return {
        "trainings": trainings_list,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total
        }
    }