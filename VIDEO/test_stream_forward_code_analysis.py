#!/usr/bin/env python3
"""
推流转发功能代码层面测试脚本
检查前后端接口匹配和逻辑完整性

@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import os
import sys
import re
import ast
from typing import Dict, List, Set, Tuple
from pathlib import Path

# 添加路径
video_root = os.path.dirname(os.path.abspath(__file__))
web_root = os.path.join(os.path.dirname(video_root), 'WEB')

# 测试结果
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'errors': []
}


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")


def print_result(success: bool, message: str, is_warning: bool = False):
    """打印测试结果"""
    if success:
        print(f"✅ {message}")
        test_results['passed'] += 1
    elif is_warning:
        print(f"⚠️  {message}")
        test_results['warnings'] += 1
    else:
        print(f"❌ {message}")
        test_results['failed'] += 1
        test_results['errors'].append(message)


def extract_routes_from_python(file_path: str) -> List[Dict]:
    """从Python文件中提取路由定义"""
    routes = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式提取路由
        # 匹配 @blueprint.route('/path', methods=['GET', 'POST'])
        pattern = r'@\w+\.route\([\'"]([^\'"]+)[\'"],\s*methods=\[([^\]]+)\]\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            path = match.group(1)
            methods_str = match.group(2)
            methods = [m.strip().strip('"\'') for m in methods_str.split(',')]
            routes.append({
                'path': path,
                'methods': methods,
                'file': file_path
            })
    except Exception as e:
        print(f"解析文件失败 {file_path}: {str(e)}")
    
    return routes


def extract_api_calls_from_typescript(file_path: str) -> List[Dict]:
    """从TypeScript文件中提取API调用"""
    api_calls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取API函数定义
        # 匹配 export const functionName = (params?: {...}) => { return commonApi(...) }
        pattern = r'export\s+const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*commonApi[^}]*\([\'"]([^\'"]+)[\'"]'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            url = match.group(2)
            api_calls.append({
                'function': func_name,
                'url': url,
                'file': file_path
            })
    except Exception as e:
        print(f"解析文件失败 {file_path}: {str(e)}")
    
    return api_calls


def test_backend_routes():
    """测试后端路由定义"""
    print_test_header("后端路由定义检查")
    
    blueprint_file = os.path.join(video_root, 'app', 'blueprints', 'stream_forward.py')
    if not os.path.exists(blueprint_file):
        print_result(False, f"后端路由文件不存在: {blueprint_file}")
        return []
    
    routes = extract_routes_from_python(blueprint_file)
    
    # 预期的路由列表
    expected_routes = [
        {'path': '/task/list', 'methods': ['GET']},
        {'path': '/task/<int:task_id>', 'methods': ['GET']},
        {'path': '/task', 'methods': ['POST']},
        {'path': '/task/<int:task_id>', 'methods': ['PUT']},
        {'path': '/task/<int:task_id>', 'methods': ['DELETE']},
        {'path': '/task/<int:task_id>/start', 'methods': ['POST']},
        {'path': '/task/<int:task_id>/stop', 'methods': ['POST']},
        {'path': '/task/<int:task_id>/restart', 'methods': ['POST']},
        {'path': '/task/<int:task_id>/status', 'methods': ['GET']},
        {'path': '/task/<int:task_id>/logs', 'methods': ['GET']},
        {'path': '/task/<int:task_id>/streams', 'methods': ['GET']},
        {'path': '/heartbeat', 'methods': ['POST']},
    ]
    
    found_routes = {}
    for route in routes:
        key = f"{route['path']}|{','.join(sorted(route['methods']))}"
        found_routes[key] = route
    
    for expected in expected_routes:
        key = f"{expected['path']}|{','.join(sorted(expected['methods']))}"
        if key in found_routes:
            print_result(True, f"路由存在: {expected['path']} [{','.join(expected['methods'])}]")
        else:
            print_result(False, f"路由缺失: {expected['path']} [{','.join(expected['methods'])}]")
    
    return routes


def test_frontend_api_calls():
    """测试前端API调用"""
    print_test_header("前端API调用检查")
    
    api_file = os.path.join(web_root, 'src', 'api', 'device', 'stream_forward.ts')
    if not os.path.exists(api_file):
        print_result(False, f"前端API文件不存在: {api_file}")
        return []
    
    api_calls = extract_api_calls_from_typescript(api_file)
    
    # 预期的API调用列表
    expected_apis = [
        {'function': 'listStreamForwardTasks', 'url': '/task/list'},
        {'function': 'getStreamForwardTask', 'url': '/task/'},
        {'function': 'createStreamForwardTask', 'url': '/task'},
        {'function': 'updateStreamForwardTask', 'url': '/task/'},
        {'function': 'deleteStreamForwardTask', 'url': '/task/'},
        {'function': 'startStreamForwardTask', 'url': '/task/'},
        {'function': 'stopStreamForwardTask', 'url': '/task/'},
        {'function': 'restartStreamForwardTask', 'url': '/task/'},
        {'function': 'getStreamForwardTaskStatus', 'url': '/task/'},
        {'function': 'getStreamForwardTaskLogs', 'url': '/task/'},
        {'function': 'getStreamForwardTaskStreams', 'url': '/task/'},
    ]
    
    found_apis = {api['function']: api for api in api_calls}
    
    for expected in expected_apis:
        if expected['function'] in found_apis:
            found_api = found_apis[expected['function']]
            if expected['url'] in found_api['url']:
                print_result(True, f"API函数存在: {expected['function']} -> {found_api['url']}")
            else:
                print_result(False, f"API函数URL不匹配: {expected['function']} -> 期望包含 {expected['url']}, 实际 {found_api['url']}")
        else:
            print_result(False, f"API函数缺失: {expected['function']}")
    
    return api_calls


def test_data_model_consistency():
    """测试数据模型一致性"""
    print_test_header("数据模型一致性检查")
    
    # 检查后端模型
    models_file = os.path.join(video_root, 'models.py')
    if not os.path.exists(models_file):
        print_result(False, f"模型文件不存在: {models_file}")
        return
    
    with open(models_file, 'r', encoding='utf-8') as f:
        models_content = f.read()
    
    # 检查StreamForwardTask模型
    if 'class StreamForwardTask' in models_content:
        print_result(True, "StreamForwardTask模型存在")
        
        # 检查必要字段
        required_fields = [
            'id', 'task_name', 'task_code', 'device_ids', 'device_names',
            'output_format', 'output_quality', 'output_bitrate',
            'status', 'is_enabled', 'run_status', 'exception_reason',
            'service_server_ip', 'service_port', 'service_process_id',
            'service_last_heartbeat', 'service_log_path',
            'total_streams', 'active_streams', 'description',
            'created_at', 'updated_at'
        ]
        
        # 检查to_dict方法
        if 'def to_dict(self):' in models_content:
            print_result(True, "to_dict方法存在")
            
            # 检查to_dict方法中是否包含所有必要字段
            to_dict_start = models_content.find('def to_dict(self):')
            if to_dict_start != -1:
                # 查找方法结束（下一个def或class）
                next_def = models_content.find('\n    def ', to_dict_start + 1)
                next_class = models_content.find('\nclass ', to_dict_start + 1)
                end_pos = min([x for x in [next_def, next_class] if x != -1] or [len(models_content)])
                to_dict_content = models_content[to_dict_start:end_pos]
                
                missing_fields = []
                for field in required_fields:
                    if f"'{field}'" not in to_dict_content and f'"{field}"' not in to_dict_content:
                        missing_fields.append(field)
                
                if missing_fields:
                    print_result(False, f"to_dict方法缺少字段: {missing_fields}")
                else:
                    print_result(True, "to_dict方法包含所有必要字段")
        else:
            print_result(False, "to_dict方法不存在")
    else:
        print_result(False, "StreamForwardTask模型不存在")
    
    # 检查前端类型定义
    api_file = os.path.join(web_root, 'src', 'api', 'device', 'stream_forward.ts')
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        if 'interface StreamForwardTask' in api_content:
            print_result(True, "前端StreamForwardTask接口存在")
            
            # 检查必要字段
            required_fields_ts = [
                'id', 'task_name', 'task_code', 'device_ids', 'device_names',
                'output_format', 'output_quality', 'output_bitrate',
                'status', 'is_enabled', 'run_status', 'exception_reason',
                'service_server_ip', 'service_port', 'service_process_id',
                'service_last_heartbeat', 'service_log_path',
                'total_streams', 'active_streams', 'description',
                'created_at', 'updated_at'
            ]
            
            missing_fields = []
            for field in required_fields_ts:
                if f'{field}:' not in api_content and f'{field}?' not in api_content:
                    missing_fields.append(field)
            
            if missing_fields:
                print_result(False, f"前端接口缺少字段: {missing_fields}")
            else:
                print_result(True, "前端接口包含所有必要字段")
        else:
            print_result(False, "前端StreamForwardTask接口不存在")


def test_service_logic():
    """测试服务逻辑完整性"""
    print_test_header("服务逻辑完整性检查")
    
    service_file = os.path.join(video_root, 'app', 'services', 'stream_forward_service.py')
    if not os.path.exists(service_file):
        print_result(False, f"服务文件不存在: {service_file}")
        return
    
    with open(service_file, 'r', encoding='utf-8') as f:
        service_content = f.read()
    
    # 检查必要的服务函数
    required_functions = [
        'create_stream_forward_task',
        'update_stream_forward_task',
        'delete_stream_forward_task',
        'get_stream_forward_task',
        'list_stream_forward_tasks',
        'start_stream_forward_task',
        'stop_stream_forward_task',
        'restart_stream_forward_task',
    ]
    
    for func in required_functions:
        if f'def {func}' in service_content:
            print_result(True, f"服务函数存在: {func}")
        else:
            print_result(False, f"服务函数缺失: {func}")
    
    # 检查启动器服务
    launcher_file = os.path.join(video_root, 'app', 'services', 'stream_forward_launcher_service.py')
    if os.path.exists(launcher_file):
        print_result(True, "启动器服务文件存在")
        
        with open(launcher_file, 'r', encoding='utf-8') as f:
            launcher_content = f.read()
        
        if 'def start_stream_forward_task' in launcher_content:
            print_result(True, "启动函数存在")
        else:
            print_result(False, "启动函数缺失")
        
        if 'def stop_stream_forward_task' in launcher_content:
            print_result(True, "停止函数存在")
        else:
            print_result(False, "停止函数缺失")
    else:
        print_result(False, "启动器服务文件不存在")
    
    # 检查守护进程
    daemon_file = os.path.join(video_root, 'app', 'services', 'stream_forward_daemon.py')
    if os.path.exists(daemon_file):
        print_result(True, "守护进程文件存在")
        
        with open(daemon_file, 'r', encoding='utf-8') as f:
            daemon_content = f.read()
        
        if 'class StreamForwardDaemon' in daemon_content:
            print_result(True, "守护进程类存在")
        else:
            print_result(False, "守护进程类不存在")
    else:
        print_result(False, "守护进程文件不存在")


def test_frontend_components():
    """测试前端组件完整性"""
    print_test_header("前端组件完整性检查")
    
    # 检查主组件
    main_component = os.path.join(web_root, 'src', 'views', 'camera', 'components', 'StreamForward', 'index.vue')
    if os.path.exists(main_component):
        print_result(True, "主组件文件存在")
        
        with open(main_component, 'r', encoding='utf-8') as f:
            component_content = f.read()
        
        # 检查必要的API调用
        required_apis = [
            'listStreamForwardTasks',
            'createStreamForwardTask',
            'updateStreamForwardTask',
            'deleteStreamForwardTask',
            'startStreamForwardTask',
            'stopStreamForwardTask',
        ]
        
        for api in required_apis:
            if api in component_content:
                print_result(True, f"组件使用API: {api}")
            else:
                print_result(False, f"组件未使用API: {api}")
    else:
        print_result(False, "主组件文件不存在")
    
    # 检查模态框组件
    modal_component = os.path.join(web_root, 'src', 'views', 'camera', 'components', 'StreamForward', 'StreamForwardModal.vue')
    if os.path.exists(modal_component):
        print_result(True, "模态框组件文件存在")
    else:
        print_result(False, "模态框组件文件不存在")
    
    # 检查数据定义文件
    data_file = os.path.join(web_root, 'src', 'views', 'camera', 'components', 'StreamForward', 'Data.tsx')
    if os.path.exists(data_file):
        print_result(True, "数据定义文件存在")
    else:
        print_result(False, "数据定义文件不存在")


def test_api_parameter_matching():
    """测试API参数匹配"""
    print_test_header("API参数匹配检查")
    
    # 读取后端路由文件
    blueprint_file = os.path.join(video_root, 'app', 'blueprints', 'stream_forward.py')
    if not os.path.exists(blueprint_file):
        print_result(False, "后端路由文件不存在")
        return
    
    with open(blueprint_file, 'r', encoding='utf-8') as f:
        blueprint_content = f.read()
    
    # 检查列表接口参数
    if 'pageNo' in blueprint_content and 'pageSize' in blueprint_content:
        print_result(True, "列表接口支持分页参数")
    else:
        print_result(False, "列表接口缺少分页参数")
    
    if 'search' in blueprint_content:
        print_result(True, "列表接口支持搜索参数")
    else:
        print_result(False, "列表接口缺少搜索参数")
    
    if 'is_enabled' in blueprint_content:
        print_result(True, "列表接口支持状态筛选参数")
    else:
        print_result(False, "列表接口缺少状态筛选参数")
    
    # 检查创建接口参数
    if "data.get('task_name')" in blueprint_content:
        print_result(True, "创建接口包含task_name参数")
    else:
        print_result(False, "创建接口缺少task_name参数")
    
    if "data.get('device_ids')" in blueprint_content:
        print_result(True, "创建接口包含device_ids参数")
    else:
        print_result(False, "创建接口缺少device_ids参数")
    
    # 检查前端API调用参数
    api_file = os.path.join(web_root, 'src', 'api', 'device', 'stream_forward.ts')
    if os.path.exists(api_file):
        with open(api_file, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        # 检查列表API参数
        if 'pageNo' in api_content and 'pageSize' in api_content:
            print_result(True, "前端列表API包含分页参数")
        else:
            print_result(False, "前端列表API缺少分页参数")
        
        if 'search' in api_content:
            print_result(True, "前端列表API包含搜索参数")
        else:
            print_result(False, "前端列表API缺少搜索参数")


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("推流转发功能代码层面测试")
    print("="*60)
    
    # 1. 测试后端路由
    backend_routes = test_backend_routes()
    
    # 2. 测试前端API调用
    frontend_apis = test_frontend_api_calls()
    
    # 3. 测试数据模型一致性
    test_data_model_consistency()
    
    # 4. 测试服务逻辑
    test_service_logic()
    
    # 5. 测试前端组件
    test_frontend_components()
    
    # 6. 测试API参数匹配
    test_api_parameter_matching()
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"✅ 通过: {test_results['passed']}")
    print(f"⚠️  警告: {test_results['warnings']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"总计: {test_results['passed'] + test_results['warnings'] + test_results['failed']}")
    
    if test_results['errors']:
        print("\n错误列表:")
        for i, error in enumerate(test_results['errors'], 1):
            print(f"  {i}. {error}")
    
    print("\n" + "="*60)
    
    # 返回退出码
    return 0 if test_results['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

