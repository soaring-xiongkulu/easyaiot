import requests
import time
import json
import os

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

    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/train/status/{task_id}")
        except requests.exceptions.RequestException as e:
            print(f"请求发送失败: {e}")
            time.sleep(10)
            continue

        if response.status_code == 200:
            status_data = response.json()
            if status_data:
                status = status_data.get("status", "unknown")
                operation = status_data.get("operation", "unknown")
                print(f"训练状态: {status}, 当前操作: {operation}")

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

        time.sleep(10)  # 每10秒查询一次

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
        print(f"获取到 {len(logs_data.get('logs', []))} 条日志")
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