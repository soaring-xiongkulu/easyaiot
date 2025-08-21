import json
import os
import shutil
import threading
import traceback
from datetime import datetime

from flask import current_app, jsonify, Blueprint, request
from ultralytics import YOLO

from app.services.model_service import ModelService
from models import db, Model, TrainingRecord

training_bp = Blueprint('training', __name__)

# 全局训练状态和进程
training_status = {}
training_processes = {}


def organize_dataset_directories(model_id, dataset_path=None):
    """组织数据集目录结构（示例函数，需根据实际实现补充）"""
    # 实际项目中应包含数据集组织逻辑
    pass


@training_bp.route('/api/model/<int:model_id>/train', methods=['POST'])
def api_start_training(model_id):
    try:
        # 获取训练参数
        data = request.get_json()
        epochs = data.get('epochs', 20)
        model_arch = data.get('model_arch', 'yolov8n.pt')
        img_size = data.get('img_size', 640)
        batch_size = data.get('batch_size', 16)
        use_gpu = data.get('use_gpu', True)
        dataset_zip_path = data.get('dataset_zip_path')  # 新增：Minio中的数据集压缩包路径

        # 检查是否已有训练在进行
        if model_id in training_status and training_status[model_id]['status'] in ['preparing', 'training']:
            return jsonify({'success': False, 'message': '训练已在进行中'})

        # 重置训练状态
        training_status[model_id] = {
            'status': 'preparing',
            'message': '准备训练数据...',
            'progress': 0,
            'log': '',
            'stop_requested': False
        }

        # 在后台线程中启动训练
        training_thread = threading.Thread(
            target=train_model,
            args=(model_id, epochs, model_arch, img_size, batch_size, use_gpu, dataset_zip_path)
        )
        training_thread.daemon = True
        training_thread.start()

        return jsonify({'success': True, 'message': '训练已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动训练失败: {str(e)}'})


@training_bp.route('/api/model/<int:model_id>/train/stop', methods=['POST'])
def api_stop_training(model_id):
    print(f"收到停止训练请求，项目ID: {model_id}")

    # 设置停止请求标志
    if model_id in training_status:
        training_status[model_id]['stop_requested'] = True
        training_status[model_id]['status'] = 'stopping'
        training_status[model_id]['message'] = '正在停止训练...'
        print("设置停止请求标志")

        # 尝试停止训练进程（如果可能）
        if model_id in training_processes:
            pass

        return jsonify({'success': True, 'message': '停止请求已发送'})
    else:
        print("没有找到训练状态")
        return jsonify({'success': False, 'message': '没有正在进行的训练'})


@training_bp.route('/api/model/<int:model_id>/train/status')
def api_train_status(model_id):
    print(f"收到训练状态查询请求，项目ID: {model_id}")
    status = training_status.get(model_id, {
        'status': 'idle',
        'message': '等待开始',
        'progress': 0
    })
    print(f"返回训练状态: {status}")
    return jsonify(status)


def train_model(model_id, epochs=20, model_arch='model/yolov8n.pt',
                img_size=640, batch_size=16, use_gpu=True, dataset_zip_path=None):
    """增强版训练函数，集成数据集下载和解压功能"""
    print(f"训练函数被调用，项目ID: {model_id}")

    # 创建训练记录对象
    training_record = None

    try:
        from app import create_app
        application = create_app()

        with application.app_context():
            # 初始化训练记录
            training_record = TrainingRecord(
                model_id=model_id,
                dataset_path='',
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

            # 更新日志函数
            def update_log(message, progress=None):
                print(f"[训练日志 {model_id}] {message}")
                training_status[model_id]['log'] += message + '\n'

                training_record.train_log += message + '\n'
                if progress is not None:
                    training_record.progress = progress
                    training_status[model_id]['progress'] = progress
                db.session.commit()

            update_log(f"开始准备训练数据，项目ID: {model_id}")

            # 获取项目信息
            model = Model.query.get(model_id)
            if not model:
                error_msg = "项目不存在"
                update_log(error_msg)
                raise Exception(error_msg)

            update_log(f"获取项目信息成功，项目名称: {model.name}")

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log(log_msg)
                return

            # 检查数据集目录是否存在
            model_dir = os.path.join(application.root_path, 'data/datasets', str(model_id))
            data_yaml_path = os.path.join(model_dir, 'data.yaml')

            # 更新训练记录中的数据集路径
            training_record.dataset_path = data_yaml_path
            db.session.commit()

            update_log(f"项目目录: {model_dir}")
            update_log(f"数据配置文件路径: {data_yaml_path}")

            update_log("检查数据集配置文件...")

            # 数据集不存在处理逻辑
            dataset_downloaded = False
            if not os.path.exists(data_yaml_path):
                log_msg = '数据集配置文件不存在，正在尝试从Minio下载数据集...'
                training_status[model_id].update({
                    'message': '正在下载数据集...',
                    'progress': 5
                })
                update_log(log_msg, progress=5)

                # 确保数据集目录存在
                os.makedirs(model_dir, exist_ok=True)

                # 从Minio下载数据集
                if dataset_zip_path:
                    # 本地压缩包路径
                    local_zip_path = os.path.join(model_dir, 'dataset.zip')

                    # Minio下载
                    update_log(f"从Minio下载数据集: {dataset_zip_path}")
                    if ModelService.download_from_minio(
                            bucket_name="dataset-bucket",
                            object_name=dataset_zip_path,
                            destination_path=local_zip_path
                    ):
                        update_log("数据集下载成功，开始解压...")

                        # 解压数据集
                        if ModelService.extract_zip(local_zip_path, model_dir):
                            update_log("数据集解压成功")
                            dataset_downloaded = True

                            # 删除压缩包释放空间
                            os.remove(local_zip_path)
                            update_log("已清理临时压缩文件")
                        else:
                            update_log("数据集解压失败")
                    else:
                        update_log("数据集下载失败")
                else:
                    update_log("未提供数据集Minio路径，无法下载")

                # 组织数据集目录结构
                if dataset_downloaded:
                    update_log("重新组织数据集目录结构...")
                    organize_dataset_directories(model_id)
                else:
                    error_msg = "无法获取数据集，请检查Minio配置或数据集路径"
                    update_log(error_msg)
                    raise Exception(error_msg)

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log(log_msg)
                return

            # 检查data.yaml文件是否存在
            if not os.path.exists(data_yaml_path):
                error_msg = "数据集配置文件不存在"
                update_log(error_msg)
                raise Exception(error_msg)

            # 更新状态：开始加载模型
            training_status[model_id].update({
                'message': '加载预训练模型...',
                'progress': 10
            })
            update_log("加载预训练YOLOv8模型...", progress=10)

            # 开始训练
            model_path = model_arch
            update_log(f"尝试加载预训练模型: {model_path}")
            model = YOLO(model_path)
            update_log(f"预训练模型加载成功! 模型路径: {model_path}")

            # 保存模型引用以便可能的停止操作
            training_processes[model_id] = model

            # 更新状态：开始训练
            training_status[model_id].update({
                'status': 'training',
                'message': '正在训练模型...',
                'progress': 15
            })
            update_log(f"开始训练模型，共{epochs}个epochs...", progress=15)

            # 训练模型
            update_log(
                f"开始训练模型，配置: 数据文件={data_yaml_path}, epochs={epochs}, 图像尺寸={img_size}x{img_size}, 批次大小={batch_size}")

            # 确定训练设备
            import torch
            if use_gpu and torch.cuda.is_available():
                device = 0
                update_log("使用GPU进行训练")
            else:
                device = 'cpu'
                update_log("使用CPU进行训练")

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
            update_log("模型训练完成!")
            update_log(f"训练结果保存路径: {os.path.join(model_dir, 'train_results')}")

            # 检查是否应该停止训练
            if training_status.get(model_id, {}).get('stop_requested'):
                log_msg = '训练已停止'
                training_status[model_id] = {
                    'status': 'stopped',
                    'message': log_msg,
                    'progress': 0,
                    'log': training_status[model_id].get('log', '') + log_msg + '\n'
                }
                update_log(log_msg)
                return

            # 更新训练状态 - 训练完成
            training_status[model_id].update({
                'status': 'completed',
                'message': '训练完成，正在保存结果...',
                'progress': 90
            })
            update_log("训练完成，正在保存结果...", progress=90)

            # 保存最佳模型
            best_model_path = os.path.join(model_dir, 'train_results', 'weights', 'best.pt')
            update_log(f"检查最佳模型文件是否存在: {best_model_path}")

            if os.path.exists(best_model_path):
                update_log(f"找到最佳模型文件，开始复制到保存目录: {best_model_path}")

                # 将最佳模型复制到模型存储目录
                model_save_dir = os.path.join(current_app.root_path, 'static', 'models', str(model_id), 'train',
                                              'weights')
                os.makedirs(model_save_dir, exist_ok=True)
                local_model_path = os.path.join(model_save_dir, 'best.pt')
                shutil.copy(best_model_path, local_model_path)

                update_log(f"模型文件已成功复制到保存目录: {model_save_dir}")

                # 更新项目信息
                model.model_path = local_model_path
                model.last_trained = datetime.now()
                db.session.commit()

                # ================= Minio上传功能 =================
                update_log("开始上传最佳模型到Minio...", progress=95)

                # 上传最佳模型
                minio_model_path = f"models/model_{model_id}/train_{training_record.id}/best.pt"
                minio_success = ModelService.upload_to_minio(
                    bucket_name="model-bucket",
                    object_name=minio_model_path,
                    file_path=local_model_path
                )

                if minio_success:
                    update_log(f"模型已成功上传至Minio: {minio_model_path}")
                    training_record.minio_model_path = minio_model_path
                else:
                    update_log("模型上传Minio失败，请检查日志")

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
                    update_log(f"训练日志已上传至Minio: {minio_log_path}")
                    training_record.minio_log_path = minio_log_path
                else:
                    update_log("训练日志上传Minio失败，请检查日志")
                # ================= Minio上传完成 =================

                # 更新训练记录中的本地模型路径
                training_record.best_model_path = local_model_path

            else:
                error_msg = "未找到训练完成的最佳模型文件"
                update_log(error_msg)
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

            update_log("模型训练完成并已保存", progress=100)
            update_log(f"训练流程结束，最终状态: {training_status[model_id]}")

    except Exception as e:
        if training_record:
            training_record.status = 'error'
            training_record.end_time = datetime.utcnow()
            training_record.error_log = f"{str(e)}\n{traceback.format_exc()}"
            db.session.commit()

        error_msg = f'训练出错: {str(e)}'
        print(error_msg)
        traceback.print_exc()

        try:
            from app import create_app
            application = create_app()
            with application.app_context():
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
            print(f'在异常处理中获取应用上下文失败: {str(inner_e)}')
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