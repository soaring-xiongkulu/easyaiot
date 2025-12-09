#!/usr/bin/env python3
"""
推流转发功能前后端测试脚本
测试前后端功能畅通性和逻辑完整性

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 添加VIDEO模块路径
video_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, video_root)

# 加载环境变量
load_dotenv()

# 配置
BASE_URL = os.getenv('VIDEO_SERVICE_URL', 'http://localhost:5000')
API_PREFIX = f'{BASE_URL}/video/stream-forward'
JWT_TOKEN = os.getenv('JWT_TOKEN', '')  # 如果需要认证，请设置JWT_TOKEN

# 测试结果统计
test_results = {
    'passed': 0,
    'failed': 0,
    'errors': []
}


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")


def print_result(success: bool, message: str):
    """打印测试结果"""
    if success:
        print(f"✅ {message}")
        test_results['passed'] += 1
    else:
        print(f"❌ {message}")
        test_results['failed'] += 1
        test_results['errors'].append(message)


def make_request(method: str, url: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
    """发送HTTP请求"""
    headers = {
        'Content-Type': 'application/json',
    }
    if JWT_TOKEN:
        headers['X-Authorization'] = f'Bearer {JWT_TOKEN}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"错误响应: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误响应: {e.response.text}")
        raise


def test_api_connection():
    """测试API连接"""
    print_test_header("API连接测试")
    try:
        response = requests.get(f'{BASE_URL}/actuator/health', timeout=5)
        success = response.status_code == 200
        print_result(success, f"API服务连接: {response.status_code}")
        return success
    except Exception as e:
        print_result(False, f"API服务连接失败: {str(e)}")
        return False


def test_list_tasks():
    """测试获取任务列表"""
    print_test_header("获取推流转发任务列表")
    try:
        # 测试基本查询
        result = make_request('GET', f'{API_PREFIX}/task/list', params={'pageNo': 1, 'pageSize': 10})
        success = result.get('code') == 0 and 'data' in result and 'total' in result
        print_result(success, f"获取任务列表: code={result.get('code')}, total={result.get('total', 0)}")
        
        # 测试搜索功能
        result = make_request('GET', f'{API_PREFIX}/task/list', params={'pageNo': 1, 'pageSize': 10, 'search': 'test'})
        success = result.get('code') == 0
        print_result(success, f"搜索任务: code={result.get('code')}")
        
        # 测试状态筛选
        result = make_request('GET', f'{API_PREFIX}/task/list', params={'pageNo': 1, 'pageSize': 10, 'is_enabled': 1})
        success = result.get('code') == 0
        print_result(success, f"状态筛选: code={result.get('code')}")
        
        return result.get('data', [])
    except Exception as e:
        print_result(False, f"获取任务列表失败: {str(e)}")
        return []


def test_create_task(device_ids: Optional[list] = None):
    """测试创建任务"""
    print_test_header("创建推流转发任务")
    try:
        # 如果没有提供设备ID，先获取一个设备
        if not device_ids:
            # 尝试从设备列表获取一个设备ID（这里需要调用设备API）
            # 为了测试，我们使用一个示例设备ID
            device_ids = []
        
        task_data = {
            'task_name': f'测试任务_{int(time.time())}',
            'device_ids': device_ids,
            'output_format': 'rtmp',
            'output_quality': 'high',
            'description': '这是一个测试任务',
            'is_enabled': False
        }
        
        result = make_request('POST', f'{API_PREFIX}/task', data=task_data)
        success = result.get('code') == 0 and 'data' in result
        if success:
            task = result['data']
            print_result(True, f"创建任务成功: id={task.get('id')}, name={task.get('task_name')}")
            return task
        else:
            print_result(False, f"创建任务失败: {result.get('msg')}")
            return None
    except Exception as e:
        print_result(False, f"创建任务失败: {str(e)}")
        return None


def test_get_task(task_id: int):
    """测试获取任务详情"""
    print_test_header(f"获取任务详情 (ID: {task_id})")
    try:
        result = make_request('GET', f'{API_PREFIX}/task/{task_id}')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            task = result['data']
            # 验证必要字段
            required_fields = ['id', 'task_name', 'task_code', 'device_ids', 'device_names', 
                            'output_format', 'output_quality', 'is_enabled', 'run_status']
            missing_fields = [f for f in required_fields if f not in task]
            
            if missing_fields:
                print_result(False, f"缺少必要字段: {missing_fields}")
            else:
                print_result(True, f"获取任务详情成功: {task.get('task_name')}")
                print(f"  任务编号: {task.get('task_code')}")
                print(f"  关联设备: {len(task.get('device_ids', []))} 个")
                print(f"  输出格式: {task.get('output_format')}")
                print(f"  输出质量: {task.get('output_quality')}")
                print(f"  运行状态: {task.get('run_status')}")
        else:
            print_result(False, f"获取任务详情失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"获取任务详情失败: {str(e)}")


def test_update_task(task_id: int):
    """测试更新任务"""
    print_test_header(f"更新任务 (ID: {task_id})")
    try:
        update_data = {
            'task_name': f'更新后的任务_{int(time.time())}',
            'description': '这是更新后的描述',
            'output_quality': 'medium'
        }
        
        result = make_request('PUT', f'{API_PREFIX}/task/{task_id}', data=update_data)
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            task = result['data']
            print_result(True, f"更新任务成功: {task.get('task_name')}")
        else:
            print_result(False, f"更新任务失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"更新任务失败: {str(e)}")


def test_start_task(task_id: int):
    """测试启动任务"""
    print_test_header(f"启动任务 (ID: {task_id})")
    try:
        result = make_request('POST', f'{API_PREFIX}/task/{task_id}/start')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            task = result['data']
            already_running = task.get('already_running', False)
            if already_running:
                print_result(True, "任务已在运行中")
            else:
                print_result(True, "任务启动成功")
                print(f"  运行状态: {task.get('run_status')}")
        else:
            print_result(False, f"启动任务失败: {result.get('msg')}")
        
        # 等待一段时间让服务启动
        time.sleep(2)
    except Exception as e:
        print_result(False, f"启动任务失败: {str(e)}")


def test_get_task_status(task_id: int):
    """测试获取任务状态"""
    print_test_header(f"获取任务状态 (ID: {task_id})")
    try:
        result = make_request('GET', f'{API_PREFIX}/task/{task_id}/status')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            status = result['data']
            print_result(True, f"获取任务状态成功")
            print(f"  服务状态: {status.get('status')}")
            print(f"  运行状态: {status.get('run_status')}")
            print(f"  活跃流数: {status.get('active_streams', 0)}/{status.get('total_streams', 0)}")
            if status.get('server_ip'):
                print(f"  服务器IP: {status.get('server_ip')}")
            if status.get('port'):
                print(f"  端口: {status.get('port')}")
            if status.get('process_id'):
                print(f"  进程ID: {status.get('process_id')}")
        else:
            print_result(False, f"获取任务状态失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"获取任务状态失败: {str(e)}")


def test_get_task_logs(task_id: int):
    """测试获取任务日志"""
    print_test_header(f"获取任务日志 (ID: {task_id})")
    try:
        result = make_request('GET', f'{API_PREFIX}/task/{task_id}/logs', params={'lines': 50})
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            log_data = result['data']
            print_result(True, f"获取任务日志成功")
            print(f"  日志文件: {log_data.get('log_file')}")
            print(f"  总行数: {log_data.get('total_lines', 0)}")
            logs = log_data.get('logs', '')
            if logs:
                print(f"  日志内容预览 (前500字符):")
                print(f"  {logs[:500]}...")
            else:
                print("  日志为空（可能服务还未生成日志）")
        else:
            print_result(False, f"获取任务日志失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"获取任务日志失败: {str(e)}")


def test_get_task_streams(task_id: int):
    """测试获取任务推流地址"""
    print_test_header(f"获取任务推流地址 (ID: {task_id})")
    try:
        result = make_request('GET', f'{API_PREFIX}/task/{task_id}/streams')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            streams = result['data']
            print_result(True, f"获取推流地址成功: {len(streams)} 个流")
            for i, stream in enumerate(streams[:3], 1):  # 只显示前3个
                print(f"  流 {i}:")
                print(f"    设备ID: {stream.get('device_id')}")
                print(f"    设备名称: {stream.get('device_name')}")
                print(f"    RTMP流: {stream.get('rtmp_stream', 'N/A')}")
                print(f"    HTTP流: {stream.get('http_stream', 'N/A')}")
        else:
            print_result(False, f"获取推流地址失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"获取推流地址失败: {str(e)}")


def test_stop_task(task_id: int):
    """测试停止任务"""
    print_test_header(f"停止任务 (ID: {task_id})")
    try:
        result = make_request('POST', f'{API_PREFIX}/task/{task_id}/stop')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            task = result['data']
            print_result(True, "任务停止成功")
            print(f"  运行状态: {task.get('run_status')}")
        else:
            print_result(False, f"停止任务失败: {result.get('msg')}")
        
        # 等待一段时间让服务停止
        time.sleep(1)
    except Exception as e:
        print_result(False, f"停止任务失败: {str(e)}")


def test_restart_task(task_id: int):
    """测试重启任务"""
    print_test_header(f"重启任务 (ID: {task_id})")
    try:
        result = make_request('POST', f'{API_PREFIX}/task/{task_id}/restart')
        success = result.get('code') == 0 and 'data' in result
        
        if success:
            task = result['data']
            print_result(True, "任务重启成功")
            print(f"  运行状态: {task.get('run_status')}")
        else:
            print_result(False, f"重启任务失败: {result.get('msg')}")
        
        # 等待一段时间让服务重启
        time.sleep(2)
    except Exception as e:
        print_result(False, f"重启任务失败: {str(e)}")


def test_delete_task(task_id: int):
    """测试删除任务"""
    print_test_header(f"删除任务 (ID: {task_id})")
    try:
        result = make_request('DELETE', f'{API_PREFIX}/task/{task_id}')
        success = result.get('code') == 0
        
        if success:
            print_result(True, "任务删除成功")
        else:
            print_result(False, f"删除任务失败: {result.get('msg')}")
    except Exception as e:
        print_result(False, f"删除任务失败: {str(e)}")


def test_data_format_consistency():
    """测试数据格式一致性"""
    print_test_header("数据格式一致性测试")
    try:
        # 获取任务列表
        result = make_request('GET', f'{API_PREFIX}/task/list', params={'pageNo': 1, 'pageSize': 1})
        
        if result.get('code') == 0 and result.get('data'):
            task = result['data'][0]
            
            # 检查必要字段
            required_fields = [
                'id', 'task_name', 'task_code', 'device_ids', 'device_names',
                'output_format', 'output_quality', 'is_enabled', 'run_status',
                'total_streams', 'active_streams', 'created_at', 'updated_at'
            ]
            
            missing_fields = [f for f in required_fields if f not in task]
            if missing_fields:
                print_result(False, f"缺少必要字段: {missing_fields}")
            else:
                print_result(True, "数据格式完整")
            
            # 检查字段类型
            type_checks = [
                ('id', int),
                ('task_name', str),
                ('task_code', str),
                ('device_ids', list),
                ('device_names', list),
                ('output_format', str),
                ('output_quality', str),
                ('is_enabled', bool),
                ('run_status', str),
                ('total_streams', int),
                ('active_streams', int),
            ]
            
            type_errors = []
            for field, expected_type in type_checks:
                if field in task and not isinstance(task[field], expected_type):
                    type_errors.append(f"{field}: 期望 {expected_type.__name__}, 实际 {type(task[field]).__name__}")
            
            if type_errors:
                print_result(False, f"字段类型错误: {type_errors}")
            else:
                print_result(True, "字段类型正确")
        else:
            print_result(False, "无法获取任务数据")
    except Exception as e:
        print_result(False, f"数据格式一致性测试失败: {str(e)}")


def test_error_handling():
    """测试错误处理"""
    print_test_header("错误处理测试")
    
    # 测试不存在的任务ID
    try:
        result = make_request('GET', f'{API_PREFIX}/task/999999')
        if result.get('code') != 0:
            print_result(True, "不存在的任务ID返回错误码")
        else:
            print_result(False, "不存在的任务ID应该返回错误码")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print_result(True, "不存在的任务ID返回404")
        else:
            print_result(False, f"不存在的任务ID返回了意外的状态码: {e.response.status_code}")
    except Exception as e:
        print_result(False, f"错误处理测试失败: {str(e)}")
    
    # 测试无效的请求数据
    try:
        result = make_request('POST', f'{API_PREFIX}/task', data={})  # 缺少必要字段
        if result.get('code') != 0:
            print_result(True, "无效请求数据返回错误码")
        else:
            print_result(False, "无效请求数据应该返回错误码")
    except Exception as e:
        print_result(False, f"错误处理测试失败: {str(e)}")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("推流转发功能前后端测试")
    print("="*60)
    
    # 1. 测试API连接
    if not test_api_connection():
        print("\n❌ API服务不可用，终止测试")
        return
    
    # 2. 测试数据格式一致性
    test_data_format_consistency()
    
    # 3. 测试错误处理
    test_error_handling()
    
    # 4. 获取现有任务列表
    existing_tasks = test_list_tasks()
    
    # 5. 创建测试任务
    test_task = test_create_task()
    if not test_task:
        print("\n⚠️  无法创建测试任务，跳过后续测试")
        return
    
    task_id = test_task['id']
    
    try:
        # 6. 获取任务详情
        test_get_task(task_id)
        
        # 7. 更新任务
        test_update_task(task_id)
        
        # 8. 启动任务
        test_start_task(task_id)
        
        # 9. 获取任务状态
        test_get_task_status(task_id)
        
        # 10. 获取任务日志
        test_get_task_logs(task_id)
        
        # 11. 获取任务推流地址
        test_get_task_streams(task_id)
        
        # 12. 重启任务
        test_restart_task(task_id)
        
        # 13. 停止任务
        test_stop_task(task_id)
        
    finally:
        # 14. 删除测试任务
        test_delete_task(task_id)
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"总计: {test_results['passed'] + test_results['failed']}")
    
    if test_results['errors']:
        print("\n错误列表:")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"  {i}. {error}")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()

