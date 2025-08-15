import requests
import time
import json
import os
import zipfile
import tempfile
import numpy as np
from PIL import Image
import base64
from io import BytesIO
import html

# 测试配置
BASE_URL = "http://localhost:5000"
TEST_MODEL_ID = "test_yolov8_model"
TEST_MODEL_NAME = "Test YOLOv8 Model"
TEST_MODEL_VERSION = "1.0.0"

def create_dummy_model():
    """
    创建一个虚拟的模型文件用于测试
    """
    # 直接使用实际的模型文件路径
    actual_model_path = "/projects/easyaiot/AI/yolov8n.pt"
    
    # 检查实际模型文件是否存在
    if not os.path.exists(actual_model_path):
        raise FileNotFoundError(f"实际模型文件未找到: {actual_model_path}")
    
    # 返回实际模型文件路径，而不是创建dummy模型
    return actual_model_path

def create_test_image():
    """
    创建一个测试图像
    """
    # 创建一个简单的测试图像
    image = Image.new('RGB', (640, 640), color=(73, 109, 137))
    # 添加一些随机形状
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.rectangle([50, 50, 200, 200], fill=(255, 0, 0))
    draw.ellipse([300, 300, 500, 500], fill=(0, 255, 0))
    
    # 转换为base64
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

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

def test_model_deployment():
    """
    测试模型部署功能
    """
    print("=== 测试模型部署 ===")
    
    # 获取实际模型文件路径
    model_file_path = create_dummy_model()
    print(f"使用实际模型文件: {model_file_path}")
    
    try:
        # 准备部署数据
        files = {
            'model_file': (
                os.path.basename(model_file_path),
                open(model_file_path, 'rb'),
                'application/octet-stream'
            )
        }
        
        data = {
            'model_id': TEST_MODEL_ID,
            'model_name': TEST_MODEL_NAME,
            'model_version': TEST_MODEL_VERSION
        }
        
        # 发送部署请求
        print("发送模型部署请求...")
        response = requests.post(
            f"{BASE_URL}/model/deploy",
            files=files,
            data=data
        )
        
        # 关闭文件
        files['model_file'][1].close()
        
        print(f"部署请求状态码: {response.status_code}")
        if response.status_code not in [200, 201]:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"部署失败: {decoded_msg}")
            return False, None
            
        deploy_result = response.json()
        print(f"部署结果: {json.dumps(deploy_result, indent=2, ensure_ascii=False)}")
        
        model_id = deploy_result.get("model_id") or TEST_MODEL_ID
        return True, model_id
        
    except Exception as e:
        print(f"部署过程中发生错误: {e}")
        return False, None

def test_model_status(model_id):
    """
    测试模型服务状态查询
    """
    print("\n=== 测试模型服务状态查询 ===")
    
    max_wait_time = 60  # 最大等待时间60秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/model/status/{model_id}")
            print(f"状态查询请求状态码: {response.status_code}")
            
            if response.status_code == 200:
                status_data = response.json()
                print(f"模型服务状态: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
                
                status = status_data.get("status")
                if status == "running":
                    print("模型服务正在运行")
                    return True
                elif status == "error":
                    print("模型服务出现错误")
                    return False
                else:
                    print(f"模型服务状态: {status}，继续等待...")
            else:
                error_msg = response.text
                # 解码Unicode转义序列
                decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
                # 处理HTML实体编码
                decoded_msg = html.unescape(decoded_msg)
                print(f"查询状态失败: {decoded_msg}")
                
        except requests.exceptions.RequestException as e:
            print(f"查询状态时发生错误: {e}")
            
        time.sleep(5)  # 等待5秒后重试
    
    print("模型服务启动超时")
    # 添加额外的诊断信息
    try:
        # 检查模型详细信息
        response = requests.get(f"{BASE_URL}/model/detail/{model_id}")
        if response.status_code == 200:
            detail_data = response.json()
            print(f"模型服务详细信息: {json.dumps(detail_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"获取模型详细信息时出错: {e}")
        
    return False

def test_model_details(model_id):
    """
    测试模型服务详细信息查询
    """
    print("\n=== 测试模型服务详细信息查询 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/model/detail/{model_id}")
        print(f"详细信息查询请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            detail_data = response.json()
            print(f"模型服务详细信息: {json.dumps(detail_data, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"查询详细信息失败: {decoded_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"查询详细信息时发生错误: {e}")
        return False

def test_model_inference(model_id):
    """
    测试模型推理功能
    """
    print("\n=== 测试模型推理功能 ===")
    
    # 创建测试图像
    test_image = create_test_image()
    
    # 准备推理数据
    inference_data = {
        "image": test_image
    }
    
    try:
        # 发送推理请求
        print("发送推理请求...")
        response = requests.post(
            f"{BASE_URL}/model/{model_id}/predict",
            json=inference_data
        )
        
        print(f"推理请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            inference_result = response.json()
            print("推理成功!")
            print(f"推理结果: {json.dumps(inference_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"推理失败: {decoded_msg}")
            # 对于新部署的模型，首次推理可能需要更多时间加载，可以重试
            print("等待一段时间后重试...")
            time.sleep(10)
            
            response = requests.post(
                f"{BASE_URL}/model/{model_id}/predict",
                json=inference_data
            )
            
            if response.status_code == 200:
                inference_result = response.json()
                print("重试后推理成功!")
                print(f"推理结果: {json.dumps(inference_result, indent=2, ensure_ascii=False)}")
                return True
            else:
                error_msg = response.text
                # 解码Unicode转义序列
                decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
                # 处理HTML实体编码
                decoded_msg = html.unescape(decoded_msg)
                print(f"重试后仍然失败: {decoded_msg}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"推理过程中发生错误: {e}")
        return False

def test_model_list():
    """
    测试模型服务列表查询
    """
    print("\n=== 测试模型服务列表查询 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/model/list")
        print(f"列表查询请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            list_data = response.json()
            print(f"模型服务列表: {json.dumps(list_data, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"查询列表失败: {decoded_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"查询列表时发生错误: {e}")
        return False

def test_stop_model_service(model_id):
    """
    测试停止模型服务
    """
    print("\n=== 测试停止模型服务 ===")
    
    try:
        response = requests.post(f"{BASE_URL}/model/stop/{model_id}")
        print(f"停止服务请求状态码: {response.status_code}")
        
        if response.status_code == 200:
            stop_result = response.json()
            print(f"停止服务结果: {json.dumps(stop_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"停止服务失败: {decoded_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"停止服务时发生错误: {e}")
        return False

def test_model_redployment(model_id):
    """
    测试重新部署已停止的模型服务
    """
    print("\n=== 测试重新部署已停止的模型服务 ===")
    
    try:
        # 准备部署数据（不上传文件，使用已存在的模型）
        data = {
            'model_id': model_id,
            'model_name': TEST_MODEL_NAME,
            'model_version': TEST_MODEL_VERSION
        }
        
        # 发送部署请求
        print("发送模型重新部署请求...")
        response = requests.post(
            f"{BASE_URL}/model/deploy",
            data=data
        )
        
        print(f"重新部署请求状态码: {response.status_code}")
        if response.status_code not in [200, 201]:
            error_msg = response.text
            # 解码Unicode转义序列
            decoded_msg = error_msg.encode('utf-8').decode('unicode_escape')
            # 处理HTML实体编码
            decoded_msg = html.unescape(decoded_msg)
            print(f"重新部署失败: {decoded_msg}")
            return False
            
        deploy_result = response.json()
        print(f"重新部署结果: {json.dumps(deploy_result, indent=2, ensure_ascii=False)}")
        return True
        
    except Exception as e:
        print(f"重新部署过程中发生错误: {e}")
        return False

def main():
    """
    主测试函数
    """
    print("开始测试模型服务部署和推理接口")
    
    # 检查服务是否可用
    if not check_service_availability():
        print("错误: AI服务不可用，请确保服务正在运行后再执行测试。")
        print("可以通过以下命令启动服务:")
        print("  cd /projects/easyaiot/AI")
        print("  python app.py")
        return
    
    # 1. 测试模型部署
    success, model_id = test_model_deployment()
    if not success or not model_id:
        print("模型部署测试失败，退出测试")
        return
    
    # 2. 测试模型状态
    if not test_model_status(model_id):
        print("模型状态检查失败")
        return
    
    # 3. 测试模型详细信息
    if not test_model_details(model_id):
        print("模型详细信息查询失败")
    
    # 4. 测试模型列表
    if not test_model_list():
        print("模型列表查询失败")
    
    # 5. 测试模型推理
    if not test_model_inference(model_id):
        print("模型推理测试失败")
    
    # 6. 测试停止模型服务
    if not test_stop_model_service(model_id):
        print("停止模型服务测试失败")
    
    # 7. 测试重新部署
    if not test_model_redployment(model_id):
        print("重新部署模型服务测试失败")
    
    print("\n=== 所有测试完成 ===")

if __name__ == "__main__":
    main()