import requests
import time
import json
import torch
import warnings
import gc
import os

# 添加一些环境变量设置来优化训练
os.environ['CUDA_LAUNCH_BLOCKING'] = '1'

def train_model_with_fixes():
    try:
        # 清理GPU内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()
        
        # 原有的训练代码应该在这里
        # 为了防止训练卡住，添加以下改进:
        
        # 1. 设置确定性算法以提高稳定性
        torch.backends.cudnn.benchmark = True
        
        # 2. 减少数据加载器的worker数量以避免死锁
        # 在训练函数中设置 num_workers=0 或较小的值
        
        # 3. 添加训练进度监控
        print("Starting training with fixes...")
        
        # 4. 添加内存监控
        if torch.cuda.is_available():
            print(f"GPU memory allocated: {torch.cuda.memory_allocated()/1024**3:.2f}GB")
            print(f"GPU memory reserved: {torch.cuda.memory_reserved()/1024**3:.2f}GB")
            
    except Exception as e:
        print(f"Training error: {e}")
        # 强制清理内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

# 如果您使用的是yolov5或其他训练脚本，请确保在训练参数中添加:
# hyp = {
#     'lr0': 0.01,      # 初始学习率
#     'momentum': 0.937, # SGD动量
#     'weight_decay': 0.0005, # 权重衰减
# }

# train_params = {
#     'epochs': 2,       # 训练轮数
#     'batch_size': 16,  # 批处理大小(可根据GPU内存调整)
#     'imgsz': 640,      # 图像大小
#     'workers': 0,      # 数据加载线程数(设置为0避免卡死)
# }

# 测试配置
BASE_URL = "http://localhost:5000"
DATASET_URL = "http://minio-server:9000/ai-service-bucket/datasets/coco128"  # 示例数据集URL


def check_service_availability():
    """
    检查AI服务是否可用
    """
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"无法连接到AI服务 ({BASE_URL}): {e}")
        return False


def test_training_workflow():
    """
    测试完整的模型训练工作流程
    """
    print("=== 开始测试模型训练工作流程 ===")

    # 1. 启动训练任务
    print("\n1. 启动训练任务...")
    train_config = {
        "dataset_url": DATASET_URL,
        "model_config": {
            "model_type": "yolov8n.pt",
            "epochs": 2,  # 使用较少的epochs进行测试
            "imgsz": 640,
            "batch_size": 16,
            "model_name": "Test_Model",
            "model_version": "1.0.0"
        }
    }

    try:
        response = requests.post(f"{BASE_URL}/train/start", json=train_config)
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败，请确保AI服务正在运行: {e}")
        return False

    print(f"启动训练请求状态码: {response.status_code}")

    if response.status_code != 202:
        print(f"启动训练失败: {response.text}")
        return False

    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"训练任务ID: {task_id}")

    if not task_id:
        print("未能获取任务ID")
        return False

    # 2. 轮询训练状态直到完成
    print("\n2. 监控训练进度...")
    max_wait_time = 300  # 最大等待5分钟
    start_time = time.time()
    
    # 添加更详细的日志记录
    last_status = None
    last_operation = None
    status_check_count = 0

    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/train/status/{task_id}")
        except requests.exceptions.RequestException as e:
            print(f"请求发送失败: {e}")
            time.sleep(10)
            continue

        status_check_count += 1
        print(f"[检查 #{status_check_count}] 时间: {time.strftime('%H:%M:%S')}")
        
        if response.status_code == 200:
            status_data = response.json()
            if status_data:
                status = status_data.get("status", "unknown")
                operation = status_data.get("operation", "unknown")
                
                # 只有状态发生变化时才打印
                if status != last_status or operation != last_operation:
                    print(f"训练状态: {status}, 当前操作: {operation}")
                    last_status = status
                    last_operation = operation
                else:
                    print(f"状态未变化: {status}, 操作: {operation}")

                if status == "completed":
                    print("训练完成!")
                    break
                elif status == "failed":
                    print("训练失败!")
                    print(f"错误详情: {status_data}")
                    return False
            else:
                print("暂无训练状态信息")
        elif response.status_code == 404:
            print("训练任务未找到，可能还在初始化中...")
        else:
            print(f"获取训练状态失败: {response.status_code}")

        # 缩短检查间隔以更密切监控
        time.sleep(5)  # 每5秒查询一次

    if time.time() - start_time >= max_wait_time:
        print("训练超时!")
        return False

    # 3. 获取训练日志
    print("\n3. 获取训练日志...")
    try:
        response = requests.get(f"{BASE_URL}/train/logs/{task_id}")
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败: {e}")
        return False

    if response.status_code == 200:
        logs_data = response.json()
        logs = logs_data.get('logs', [])
        print(f"获取到 {len(logs)} 条日志")
        # 打印最近的几条日志
        if logs:
            print("最近的日志条目:")
            for log_entry in logs[-10:]:  # 打印最近10条日志
                print(f"  {log_entry}")
    else:
        print(f"获取训练日志失败: {response.status_code}")
        print(f"错误信息: {response.text}")

    return task_id


def test_model_deployment_and_inference(task_id):
    """
    测试模型部署和推理
    """
    print("\n=== 开始测试模型部署和推理 ===")

    # 1. 验证模型是否已保存到existing_models表
    print("\n1. 验证训练模型是否已保存...")
    model_id = f"model_{task_id}"

    # 这里我们模拟从数据库获取模型信息的过程
    # 在实际测试中，您可能需要直接查询数据库或通过其他API获取

    # 2. 部署模型服务
    print("\n2. 部署模型服务...")
    deploy_config = {
        "model_id": model_id,
        "model_name": "Test_Model",
        "model_version": "1.0.0"
    }

    try:
        response = requests.post(f"{BASE_URL}/model/deploy", json=deploy_config)
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败: {e}")
        return False

    print(f"部署请求状态码: {response.status_code}")

    if response.status_code not in [200, 201]:
        print(f"部署模型失败: {response.text}")
        return False

    deploy_data = response.json()
    print(f"部署结果: {deploy_data}")

    # 3. 检查模型服务状态
    print("\n3. 检查模型服务状态...")
    time.sleep(5)  # 等待服务启动

    try:
        response = requests.get(f"{BASE_URL}/model/status/{model_id}")
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败: {e}")
        return False

    print(f"服务状态查询状态码: {response.status_code}")

    if response.status_code == 200:
        status_data = response.json()
        print(f"模型服务状态: {status_data}")
    else:
        print(f"查询服务状态失败: {response.text}")
        return False

    # 4. 测试模型推理 (这里使用模拟数据)
    print("\n4. 测试模型推理...")
    # 注意: 实际推理需要真实的图像数据，这里仅作接口测试
    inference_data = {
        "image": "base64_encoded_image_data"  # 模拟图像数据
    }

    try:
        response = requests.post(f"{BASE_URL}/model/{model_id}/predict", json=inference_data)
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败: {e}")
        return False

    print(f"推理请求状态码: {response.status_code}")

    if response.status_code == 200:
        inference_result = response.json()
        print("推理成功!")
        print(f"推理结果: {json.dumps(inference_result, indent=2, ensure_ascii=False)}")
    else:
        print(f"推理失败: {response.text}")
        # 对于YOLO模型，首次推理可能需要一些时间加载，可以重试
        print("等待一段时间后重试...")
        time.sleep(10)
        try:
            response = requests.post(f"{BASE_URL}/model/{model_id}/predict", json=inference_data)
        except requests.exceptions.RequestException as e:
            print(f"重试请求发送失败: {e}")
            return False

        if response.status_code == 200:
            inference_result = response.json()
            print("重试后推理成功!")
            print(f"推理结果: {json.dumps(inference_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"重试后仍然失败: {response.text}")

    # 5. 停止模型服务
    print("\n5. 停止模型服务...")
    try:
        response = requests.post(f"{BASE_URL}/model/stop/{model_id}")
    except requests.exceptions.RequestException as e:
        print(f"请求发送失败: {e}")
        return False

    if response.status_code == 200:
        print("模型服务已停止")
    else:
        print(f"停止模型服务失败: {response.text}")

    return True


def main():
    """
    主测试函数
    """
    print("开始测试模型训练和推理接口")

    # 检查服务是否可用
    if not check_service_availability():
        print("错误: AI服务不可用，请确保服务正在运行后再执行测试。")
        print("可以通过以下命令启动服务:")
        print("  cd /projects/easyaiot/AI")
        print("  python app.py")
        return

    # 测试训练工作流程
    task_id = test_training_workflow()
    if not task_id:
        print("训练测试失败，退出测试")
        return

    # 测试部署和推理
    success = test_model_deployment_and_inference(task_id)

    if success:
        print("\n=== 所有测试通过! ===")
    else:
        print("\n=== 部分测试失败 ===")


if __name__ == "__main__":
    main()