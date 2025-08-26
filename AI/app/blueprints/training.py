import json
import os
import shutil
import threading
import traceback
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import torch
from flask import current_app, jsonify, Blueprint, request
from ultralytics import YOLO

from app.services.model_service import ModelService
from models import db, Model, TrainingRecord

training_bp = Blueprint('training', __name__)

# 全局训练状态和进程
training_status = {}
training_processes = {}


@training_bp.route('/<int:model_id>/train', methods=['POST'])
def api_start_training(model_id):
    try:
        # 获取训练参数
        data = request.get_json()

        record_id = data.get('taskId')  # 获取前端传递的taskId
        # 参数映射（前端 -> 后端）
        epochs = data.get('epochs', 20)
        batch_size = data.get('batch_size', 16)
        img_size = data.get('imgsz', 640)  # 注意前端参数名为imgsz
        model_arch = data.get('modelPath', 'yolov8n.pt')
        dataset_url = data.get('datasetPath')  # 前端传递的下载URL

        # 处理模型路径 - 使用相对于根路径的model/yolov8n.pt
        if not model_arch or model_arch == 'yolov8n.pt':
            model_arch = os.path.join('model', 'yolov8n.pt')

        # 从URL解析Minio对象路径
        dataset_zip_path = dataset_url
        use_gpu = data.get('use_gpu', True)  # 默认使用GPU

        # 检查是否已有训练在进行
        if model_id in training_status and training_status[model_id]['status'] in ['preparing', 'training']:
            return jsonify({'success': False, 'code': 0, 'msg': '训练已在进行中'}), 200

        # 立即保存数据集路径到数据库
        training_record = None
        if record_id:
            training_record = TrainingRecord.query.get(record_id)
            if training_record:
                training_record.dataset_path = dataset_zip_path  # 保存Minio路径
                training_record.start_time = datetime.utcnow()
                training_record.status = 'preparing'
                training_record.train_log = ''
                training_record.error_log = None
                training_record.progress = 0
                training_record.hyperparameters = json.dumps({
                    'epochs': epochs,
                    'model_arch': model_arch,
                    'img_size': img_size,
                    'batch_size': batch_size,
                    'use_gpu': use_gpu
                })
                db.session.commit()

        if not training_record:
            training_record = TrainingRecord(
                model_id=model_id,
                dataset_path=dataset_zip_path,  # ⭐ 直接保存Minio路径 ⭐
                hyperparameters=json.dumps({
                    'epochs': epochs,
                    'model_arch': model_arch,
                    'img_size': img_size,
                    'batch_size': batch_size,
                    'use_gpu': use_gpu
                }),
                start_time=datetime.utcnow(),
                status='preparing',
                train_log='',
                checkpoint_dir=''
            )
            db.session.add(training_record)
            db.session.commit()

        # 重置训练状态
        training_status[model_id] = {
            'status': 'preparing',
            'message': '准备训练数据...',
            'progress': 0,
            'log': '',
            'stop_requested': False
        }

        # 在后台线程中启动训练，传递training_record.id
        training_thread = threading.Thread(
            target=train_model,
            args=(model_id, epochs, model_arch, img_size, batch_size,
                  use_gpu, dataset_zip_path, training_record.id)  # 添加record_id参数
        )
        training_thread.daemon = True
        training_thread.start()

        return jsonify({
            'success': True,
            'code': 0,
            'msg': '训练已启动',
            'record_id': training_record.id  # 返回记录ID给前端
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'code': 400, 'msg': f'启动训练失败: {str(e)}'}), 400


def get_project_root():
    """获取项目根目录"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))


@training_bp.route('/<int:model_id>/train/stop', methods=['POST'])
def api_stop_training(model_id):
    update_log(f"收到停止训练请求，项目ID: {model_id}", model_id)

    # 设置停止请求标志
    if model_id in training_status:
        training_status[model_id]['stop_requested'] = True
        training_status[model_id]['status'] = 'stopping'
        training_status[model_id]['message'] = '正在停止训练...'
        update_log("设置停止请求标志", model_id)

        # 尝试停止训练进程（如果可能）
        if model_id in training_processes:
            pass

        return jsonify({'success': True, 'code': 0, 'msg': '停止请求已发送'}), 200
    else:
        update_log("没有找到训练状态", model_id)
        return jsonify({'success': False, 'code': 0, 'msg': '没有正在进行的训练'}), 200


@training_bp.route('/<int:model_id>/train/status')
def api_train_status(model_id):
    update_log(f"收到训练状态查询请求，项目ID: {model_id}", model_id)
    status = training_status.get(model_id, {
        'status': 'idle',
        'message': '等待开始',
        'progress': 0
    })
    update_log(f"返回训练状态: {status}", model_id)
    return jsonify({'status': status, 'code': 0, 'msg': '没有正在进行的训练'}), 200


def update_log(message, model_id=None, progress=None, training_record=None):
    """统一的日志记录函数"""
    log_message = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(log_message)

    # 如果提供了model_id，更新训练状态
    if model_id is not None and model_id in training_status:
        training_status[model_id]['log'] += log_message + '\n'
        if progress is not None:
            training_status[model_id]['progress'] = progress

    # 如果提供了training_record，更新数据库记录
    if training_record is not None:
        training_record.train_log += log_message + '\n'
        if progress is not None:
            training_record.progress = progress
        try:
            db.session.commit()
        except Exception as e:
            print(f"数据库提交失败: {str(e)}")


def train_model(model_id, epochs=20, model_arch='model/yolov8n.pt',
                img_size=640, batch_size=16, use_gpu=True,
                dataset_zip_path=None, record_id=None):
    """增强版训练函数，集成数据集下载和解压功能"""
    update_log(f"训练函数被调用，项目ID: {model_id}", model_id)

    try:
        from run import create_app
        application = create_app()

        with application.app_context():
            # 在函数内部通过record_id获取训练记录
            training_record = TrainingRecord.query.get(record_id)

            # 更新日志函数
            def update_log_local(message, progress=None):
                update_log(message, model_id, progress, training_record)

            update_log_local(f"开始准备训练数据，项目ID: {model_id}")

            # 获取项目信息
            model = Model.query.get(model_id)
            if not model:
                error_msg = "项目不存在"
                update_log_local(error_msg)
                training_record.status = 'error'
                training_record.error_log = error_msg
                db.session.commit()
                raise Exception(error_msg)

            update_log_local(f"获取项目信息成功，项目名称: {model.name}")

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            # data/datasets/123/
            # ├── images /
            # │   ├── train /
            # │   └── val /
            # ├── labels /
            # │   ├── train /
            # │   └── val /
            # └── data.yaml
            # 检查数据集目录是否存在
            model_dir = os.path.join(get_project_root(), 'data/datasets', str(model_id))
            data_yaml_path = os.path.join(model_dir, 'data.yaml')

            # 检查数据集目录结构完整性
            required_dirs = ['images/train', 'images/val', 'images/test', 'labels/train', 'labels/val', 'labels/test']
            all_dirs_exist = all(os.path.exists(os.path.join(model_dir, d)) for d in required_dirs)

            if os.path.exists(data_yaml_path) and all_dirs_exist:
                # 更新训练记录中的数据集路径
                training_record.dataset_path = data_yaml_path
                db.session.commit()
                update_log_local(f"数据集验证成功，路径已更新: {data_yaml_path}")

            update_log_local(f"项目目录: {model_dir}")
            update_log_local(f"数据配置文件路径: {data_yaml_path}")
            update_log_local("检查数据集配置文件...")

            # 数据集不存在处理逻辑
            dataset_downloaded = False
            if not os.path.exists(data_yaml_path):
                log_msg = '数据集配置文件不存在，正在尝试从Minio下载数据集...'
                training_status[model_id].update({
                    'message': '正在下载数据集...',
                    'progress': 5
                })
                update_log_local(log_msg, progress=5)

                # 确保数据集目录存在
                os.makedirs(model_dir, exist_ok=True)

                # 从Minio下载数据集
                if dataset_zip_path:
                    # 解析URL获取bucket和object信息
                    parsed_url = urlparse(dataset_zip_path)
                    query_params = parse_qs(parsed_url.query)
                    object_key = query_params.get('prefix', [None])[0]

                    # 从路径中提取bucket名称（关键修复）
                    path_parts = parsed_url.path.split('/')
                    if len(path_parts) >= 5 and path_parts[3] == 'buckets':
                        bucket_name = path_parts[4]  # /api/v1/buckets/<bucket_name>/objects...
                    else:
                        bucket_name = "datasets"  # 默认值

                    # 本地压缩包路径
                    local_zip_path = os.path.join(model_dir, 'dataset.zip')

                    # Minio下载（使用解析出的bucket和object）
                    update_log_local(f"从Minio下载数据集: bucket={bucket_name}, object={object_key}")
                    if ModelService.download_from_minio(
                            bucket_name=bucket_name,  # 使用解析出的bucket
                            object_name=object_key,  # 使用prefix参数值
                            destination_path=local_zip_path
                    ):
                        update_log_local("数据集下载成功，开始解压...")

                        # 解压数据集
                        if ModelService.extract_zip(local_zip_path, model_dir):
                            update_log_local("数据集解压成功")
                            # 删除压缩包释放空间
                            os.remove(local_zip_path)
                            update_log_local("已清理临时压缩文件")
                        else:
                            update_log_local("数据集解压失败")
                    else:
                        update_log_local("数据集下载失败")
                else:
                    update_log_local("未提供数据集Minio路径，无法下载")

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            # 检查data.yaml文件是否存在
            if not os.path.exists(data_yaml_path):
                error_msg = "数据集配置文件不存在"
                update_log_local(error_msg)
                training_record.status = 'error'
                training_record.error_log = error_msg
                db.session.commit()
                raise Exception(error_msg)

            # 更新状态：开始加载模型
            training_status[model_id].update({
                'message': '加载预训练模型...',
                'progress': 10
            })
            update_log_local("加载预训练YOLOv8模型...", progress=10)

            # 开始训练
            model_path = os.path.join(get_project_root(), model_arch)
            update_log_local(f"尝试加载预训练模型: {model_path}")
            model = YOLO(model_path)
            update_log_local(f"预训练模型加载成功! 模型路径: {model_path}")

            # 保存模型引用以便可能的停止操作
            training_processes[model_id] = model

            # 更新状态：开始训练
            training_status[model_id].update({
                'status': 'training',
                'message': '正在训练模型...',
                'progress': 15
            })
            update_log_local(f"开始训练模型，共{epochs}个epochs...", progress=15)

            # 训练模型
            update_log_local(
                f"开始训练模型，配置: 数据文件={data_yaml_path}, epochs={epochs}, 图像尺寸={img_size}x{img_size}, 批次大小={batch_size}")

            # 在训练函数开始处添加GPU状态检查
            gpu_status = check_gpu_status()
            update_log_local(f"GPU状态检查: {json.dumps(gpu_status, indent=2)}")

            # 确定训练设备
            if use_gpu:
                if torch.cuda.is_available():
                    device = 0
                    update_log_local(f"使用GPU进行训练: {torch.cuda.get_device_name(0)}")
                else:
                    device = 'cpu'
                    update_log_local("警告: 请求使用GPU，但CUDA不可用。使用CPU进行训练。")
                    # 记录详细原因
                    update_log_local(
                        f"可能的原因: PyTorch版本={torch.__version__}, CUDA编译版本={getattr(torch.version, 'cuda', '未知')}")
            else:
                device = 'cpu'
                update_log_local("使用CPU进行训练")

            # 设置检查点目录
            checkpoint_dir = os.path.join(model_dir, 'train_results', 'checkpoints')
            os.makedirs(checkpoint_dir, exist_ok=True)
            training_record.checkpoint_dir = checkpoint_dir
            db.session.commit()

            # 训练模型
            results = model.train(
                data=data_yaml_path,
                epochs=epochs,
                imgsz=img_size,
                batch=batch_size,
                project=model_dir,
                name='train_results',
                exist_ok=True,
                device=device,
                save_period=5
            )

            # 解析训练结果（results.csv），并人性化的保存到日志中
            results_csv_path = os.path.join(model_dir, 'train_results', 'results.csv')
            if os.path.exists(results_csv_path):
                import pandas as pd
                try:
                    # 读取CSV文件
                    df = pd.read_csv(results_csv_path)
                    
                    # 生成人性化的训练报告
                    log_lines = ["\n=== 训练结果概览 ==="]
                    log_lines.append(f"总共完成 {len(df)} 个epochs")
                    
                    if not df.empty:
                        last_epoch = df.iloc[-1]
                        log_lines.append("\n--- 最终训练指标 ---")
                        log_lines.append(f"Epoch: {last_epoch.get('epoch', 'N/A')}")
                        log_lines.append(f"训练损失: {last_epoch.get('train/box_loss', 'N/A'):.6f} (边界框), "
                                        f"{last_epoch.get('train/cls_loss', 'N/A'):.6f} (分类), "
                                        f"{last_epoch.get('train/dfl_loss', 'N/A'):.6f} (分布焦点)")
                        log_lines.append(f"验证损失: {last_epoch.get('val/box_loss', 'N/A'):.6f} (边界框), "
                                        f"{last_epoch.get('val/cls_loss', 'N/A'):.6f} (分类), "
                                        f"{last_epoch.get('val/dfl_loss', 'N/A'):.6f} (分布焦点)")
                        
                        # mAP指标
                        log_lines.append("\n--- 模型性能指标 (mAP) ---")
                        log_lines.append(f"mAP@0.5: {last_epoch.get('metrics/mAP50(B)', 'N/A'):.4f}")
                        log_lines.append(f"mAP@0.5:0.95: {last_epoch.get('metrics/mAP50-95(B)', 'N/A'):.4f}")
                        
                        # 精确度和召回率
                        log_lines.append("\n--- 精确度与召回率 ---")
                        log_lines.append(f"精确度(Precision): {last_epoch.get('metrics/Precision(B)', 'N/A'):.4f}")
                        log_lines.append(f"召回率(Recall): {last_epoch.get('metrics/Recall(B)', 'N/A'):.4f}")
                        log_lines.append(f"F1-Score: {last_epoch.get('metrics/F1(B)', 'N/A'):.4f}")
                        
                        # 训练时间信息
                        if 'elapsed_time' in df.columns:
                            total_time = df['elapsed_time'].sum()
                            log_lines.append(f"\n--- 训练时间统计 ---")
                            log_lines.append(f"总训练时间: {total_time:.2f} 秒")
                            log_lines.append(f"平均每个epoch耗时: {total_time/len(df):.2f} 秒")
                        
                        # 最佳模型信息
                        if 'metrics/mAP50(B)' in df.columns:
                            best_map50 = df['metrics/mAP50(B)'].max()
                            best_epoch = df['metrics/mAP50(B)'].idxmax()
                            log_lines.append(f"\n--- 最佳模型信息 ---")
                            log_lines.append(f"最佳mAP@0.5: {best_map50:.4f} (在epoch {best_epoch})")
                    
                    log_lines.append("\n=== 训练结果解析完成 ===\n")
                    update_log_local("\n".join(log_lines))
                    
                except Exception as e:
                    update_log_local(f"解析训练结果时出错: {str(e)}")
            else:
                update_log_local("未找到训练结果文件 results.csv")

            update_log_local("模型训练完成!")
            update_log_local(f"训练结果保存路径: {os.path.join(model_dir, 'train_results')}")

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log_local(log_msg)
                return

            # 更新训练状态 - 训练完成
            training_status[model_id].update({
                'status': 'completed',
                'message': '训练完成，正在保存结果...',
                'progress': 90
            })
            update_log_local("训练完成，正在保存结果...", progress=90)

            # 保存最佳模型
            best_model_path = os.path.join(model_dir, 'train_results', 'weights', 'best.pt')
            update_log_local(f"检查最佳模型文件是否存在: {best_model_path}")

            if os.path.exists(best_model_path):
                update_log_local(f"找到最佳模型文件，开始复制到保存目录: {best_model_path}")

                # 将最佳模型复制到模型存储目录
                model_save_dir = os.path.join(current_app.root_path, 'static', 'models', str(model_id), 'train',
                                              'weights')
                os.makedirs(model_save_dir, exist_ok=True)
                local_model_path = os.path.join(model_save_dir, 'best.pt')
                shutil.copy(best_model_path, local_model_path)

                update_log_local(f"模型文件已成功复制到保存目录: {model_save_dir}")

                # 更新项目信息
                model.model_path = local_model_path
                model.last_trained = datetime.now()
                db.session.commit()

                # ================= Minio上传功能 =================
                update_log_local("开始上传最佳模型到Minio...", progress=95)

                # 上传最佳模型
                minio_model_path = f"models/model_{model_id}/train_{training_record.id}/best.pt"
                minio_success = ModelService.upload_to_minio(
                    bucket_name="model-bucket",
                    object_name=minio_model_path,
                    file_path=local_model_path
                )

                if minio_success:
                    update_log_local(f"模型已成功上传至Minio: {minio_model_path}")
                    training_record.minio_model_path = minio_model_path
                else:
                    update_log_local("模型上传Minio失败，请检查日志")

                # 上传训练日志
                log_content = training_record.train_log
                log_path = os.path.join(model_save_dir, f"training_log_{training_record.id}.txt")
                with open(log_path, 'w') as f:
                    f.write(log_content)

                minio_log_path = f"logs/model_{model_id}/train_{training_record.id}.txt"
                log_success = ModelService.upload_to_minio(
                    bucket_name="log-bucket",
                    object_name=minio_log_path,
                    file_path=log_path
                )

                if log_success:
                    update_log_local(f"训练日志已上传至Minio: {minio_log_path}")
                    training_record.minio_log_path = minio_log_path
                else:
                    update_log_local("训练日志上传Minio失败，请检查日志")
                # ================= Minio上传完成 =================

                # 更新训练记录中的本地模型路径
                training_record.best_model_path = local_model_path

            else:
                error_msg = "未找到训练完成的最佳模型文件"
                update_log_local(error_msg)
                training_record.status = 'error'
                training_record.error_log = error_msg
                db.session.commit()
                raise Exception(error_msg)

            # 更新训练状态 - 完成
            training_status[model_id].update({
                'status': 'completed',
                'message': '模型训练完成并已保存',
                'progress': 100
            })

            # 更新训练记录状态
            training_record.status = 'completed'
            training_record.end_time = datetime.utcnow()
            training_record.progress = 100
            db.session.commit()

            update_log_local("模型训练完成并已保存", progress=100)
            update_log_local(f"训练流程结束，最终状态: {training_status[model_id]}")

    except Exception as e:
        from run import create_app
        application = create_app()
        with application.app_context():
            if training_record:
                training_record.status = 'error'
                training_record.end_time = datetime.utcnow()
                training_record.error_log = f"{str(e)}\n{traceback.format_exc()}"
                db.session.commit()

            error_msg = f'训练出错: {str(e)}'
            update_log(error_msg, model_id)
            if training_record:
                training_record.status = 'error'
                training_record.error_log = error_msg
                db.session.commit()
            traceback.print_exc()

            try:
                log_msg = f'训练出错: {str(e)}'
                training_status[model_id].update({
                    'status': 'error',
                    'message': log_msg,
                    'progress': 0,
                    'error_details': str(e),
                    'traceback': traceback.format_exc(),
                    'log': training_status[model_id].get('log', '') + log_msg + '\n' + traceback.format_exc()
                })
                if training_record:
                    training_record.train_log += log_msg + '\n' + traceback.format_exc()
                    db.session.commit()

                model = Model.query.get_or_404(model_id)
                if model:
                    model.last_error = str(e)
                    db.session.commit()
            except Exception as inner_e:
                update_log(f'在异常处理中获取应用上下文失败: {str(inner_e)}', model_id)
                training_status[model_id].update({
                    'status': 'error',
                    'message': f'严重错误: {str(e)}',
                    'progress': 0,
                    'error_details': str(e),
                    'traceback': traceback.format_exc(),
                    'log': training_status[model_id].get('log', '') + f'严重错误: {str(e)}\n' + traceback.format_exc()
                })
    finally:
        if model_id in training_processes:
            del training_processes[model_id]


def check_gpu_status():
    """检查并记录GPU状态"""
    import torch
    status = {
        'pytorch_version': torch.__version__,
        'cuda_available': torch.cuda.is_available(),
        'cuda_version': torch.version.cuda if hasattr(torch.version, 'cuda') else '未知',
        'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            status[f'device_{i}_name'] = torch.cuda.get_device_name(i)
            status[f'device_{i}_capability'] = torch.cuda.get_device_capability(i)

    return status