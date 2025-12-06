#!/usr/bin/env python3
"""
设备区域检测前后端逻辑流畅性测试脚本
@author 翱翔的雄库鲁
@email andywebjava@163.com
@wechat EasyAIoT2025
"""
import json
import requests
import sys
from typing import Dict, List, Any

# 配置
BASE_URL = "http://localhost:5000"  # 根据实际情况修改
API_PREFIX = "/video/device-detection"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def test_api(method: str, url: str, data: Dict = None, params: Dict = None) -> Dict:
    """测试API接口"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, params=params, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=30)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, timeout=30)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, timeout=30)
        else:
            return {'error': f'不支持的HTTP方法: {method}'}
        
        try:
            result = response.json()
        except:
            result = {'code': response.status_code, 'msg': response.text}
        
        return result
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def test_1_get_device_list():
    """测试1: 获取设备列表"""
    print_section("测试1: 获取设备列表")
    
    url = f"{BASE_URL}/video/camera/devices"
    print_info(f"请求: GET {url}")
    
    result = test_api('GET', url)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return None
    
    if result.get('code') == 0 and result.get('data'):
        devices = result['data']
        print_success(f"获取设备列表成功，共 {len(devices)} 个设备")
        if devices:
            print_info(f"第一个设备: ID={devices[0].get('id')}, Name={devices[0].get('name')}")
            return devices[0].get('id')
        else:
            print_warning("设备列表为空")
            return None
    else:
        print_error(f"获取设备列表失败: {result.get('msg', '未知错误')}")
        return None

def test_2_capture_snapshot(device_id: str):
    """测试2: 抓拍设备截图"""
    print_section("测试2: 抓拍设备截图")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/snapshot"
    print_info(f"请求: POST {url}")
    
    result = test_api('POST', url)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return None, None
    
    if result.get('code') == 0 and result.get('data'):
        data = result['data']
        image_id = data.get('image_id')
        image_url = data.get('image_url')
        width = data.get('width')
        height = data.get('height')
        
        print_success(f"抓拍成功")
        print_info(f"  - Image ID: {image_id}")
        print_info(f"  - Image URL: {image_url}")
        print_info(f"  - 尺寸: {width}x{height}")
        
        return image_id, image_url
    else:
        print_error(f"抓拍失败: {result.get('msg', '未知错误')}")
        return None, None

def test_3_get_regions(device_id: str):
    """测试3: 获取设备区域列表"""
    print_section("测试3: 获取设备区域列表")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/regions"
    print_info(f"请求: GET {url}")
    
    result = test_api('GET', url)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return []
    
    if result.get('code') == 0:
        regions = result.get('data', [])
        print_success(f"获取区域列表成功，共 {len(regions)} 个区域")
        for i, region in enumerate(regions, 1):
            print_info(f"  区域{i}: {region.get('region_name')} ({region.get('region_type')})")
        return regions
    else:
        print_error(f"获取区域列表失败: {result.get('msg', '未知错误')}")
        return []

def test_4_create_region(device_id: str, image_id: int):
    """测试4: 创建检测区域"""
    print_section("测试4: 创建检测区域")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/regions"
    
    # 创建一个多边形区域（归一化坐标）
    test_region = {
        'region_name': '测试多边形区域',
        'region_type': 'polygon',
        'points': [
            {'x': 0.2, 'y': 0.2},
            {'x': 0.8, 'y': 0.2},
            {'x': 0.8, 'y': 0.8},
            {'x': 0.2, 'y': 0.8}
        ],
        'image_id': image_id,
        'color': '#FF5252',
        'opacity': 0.3,
        'is_enabled': True,
        'sort_order': 0
    }
    
    print_info(f"请求: POST {url}")
    print_info(f"数据: {json.dumps(test_region, indent=2, ensure_ascii=False)}")
    
    result = test_api('POST', url, data=test_region)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return None
    
    if result.get('code') == 0 and result.get('data'):
        region = result['data']
        region_id = region.get('id')
        print_success(f"创建区域成功，区域ID: {region_id}")
        print_info(f"  - 名称: {region.get('region_name')}")
        print_info(f"  - 类型: {region.get('region_type')}")
        print_info(f"  - 点数: {len(region.get('points', []))}")
        return region_id
    else:
        print_error(f"创建区域失败: {result.get('msg', '未知错误')}")
        return None

def test_5_create_line_region(device_id: str, image_id: int):
    """测试5: 创建线条区域"""
    print_section("测试5: 创建线条区域")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/regions"
    
    # 创建一个线条区域
    test_region = {
        'region_name': '测试线条区域',
        'region_type': 'line',
        'points': [
            {'x': 0.1, 'y': 0.5},
            {'x': 0.9, 'y': 0.5}
        ],
        'image_id': image_id,
        'color': '#4CAF50',
        'opacity': 0.5,
        'is_enabled': True,
        'sort_order': 1
    }
    
    print_info(f"请求: POST {url}")
    print_info(f"数据: {json.dumps(test_region, indent=2, ensure_ascii=False)}")
    
    result = test_api('POST', url, data=test_region)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return None
    
    if result.get('code') == 0 and result.get('data'):
        region = result['data']
        region_id = region.get('id')
        print_success(f"创建线条区域成功，区域ID: {region_id}")
        return region_id
    else:
        print_error(f"创建线条区域失败: {result.get('msg', '未知错误')}")
        return None

def test_6_update_region(region_id: int):
    """测试6: 更新区域"""
    print_section("测试6: 更新区域")
    
    url = f"{BASE_URL}{API_PREFIX}/region/{region_id}"
    
    update_data = {
        'region_name': '更新后的区域名称',
        'color': '#2196F3',
        'opacity': 0.4,
        'is_enabled': False
    }
    
    print_info(f"请求: PUT {url}")
    print_info(f"数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    result = test_api('PUT', url, data=update_data)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return False
    
    if result.get('code') == 0:
        print_success("更新区域成功")
        if result.get('data'):
            region = result['data']
            print_info(f"  - 新名称: {region.get('region_name')}")
            print_info(f"  - 新颜色: {region.get('color')}")
            print_info(f"  - 新透明度: {region.get('opacity')}")
            print_info(f"  - 启用状态: {region.get('is_enabled')}")
        return True
    else:
        print_error(f"更新区域失败: {result.get('msg', '未知错误')}")
        return False

def test_7_update_cover_image(device_id: str):
    """测试7: 更新设备封面图"""
    print_section("测试7: 更新设备封面图")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/cover-image"
    print_info(f"请求: POST {url}")
    
    result = test_api('POST', url)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return False
    
    if result.get('code') == 0 and result.get('data'):
        data = result['data']
        print_success("更新封面图成功")
        print_info(f"  - 封面图路径: {data.get('cover_image_path')}")
        print_info(f"  - 图片URL: {data.get('image_url')}")
        return True
    else:
        print_error(f"更新封面图失败: {result.get('msg', '未知错误')}")
        return False

def test_8_delete_region(region_id: int):
    """测试8: 删除区域"""
    print_section("测试8: 删除区域")
    
    url = f"{BASE_URL}{API_PREFIX}/region/{region_id}"
    print_info(f"请求: DELETE {url}")
    
    result = test_api('DELETE', url)
    
    if 'error' in result:
        print_error(f"请求失败: {result['error']}")
        return False
    
    if result.get('code') == 0:
        print_success(f"删除区域成功，区域ID: {region_id}")
        return True
    else:
        print_error(f"删除区域失败: {result.get('msg', '未知错误')}")
        return False

def test_9_validate_data_structure(device_id: str):
    """测试9: 验证数据结构一致性"""
    print_section("测试9: 验证数据结构一致性")
    
    url = f"{BASE_URL}{API_PREFIX}/device/{device_id}/regions"
    result = test_api('GET', url)
    
    if result.get('code') == 0 and result.get('data'):
        regions = result['data']
        if not regions:
            print_warning("没有区域数据，跳过验证")
            return True
        
        region = regions[0]
        required_fields = [
            'id', 'device_id', 'region_name', 'region_type', 
            'points', 'color', 'opacity', 'is_enabled', 'sort_order'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in region:
                missing_fields.append(field)
        
        if missing_fields:
            print_error(f"缺少必需字段: {', '.join(missing_fields)}")
            return False
        
        # 验证points格式
        points = region.get('points', [])
        if not isinstance(points, list):
            print_error("points字段必须是数组")
            return False
        
        if points and not isinstance(points[0], dict):
            print_error("points数组元素必须是对象")
            return False
        
        if points and ('x' not in points[0] or 'y' not in points[0]):
            print_error("points数组元素必须包含x和y字段")
            return False
        
        print_success("数据结构验证通过")
        print_info(f"  - 区域ID: {region.get('id')}")
        print_info(f"  - 区域名称: {region.get('region_name')}")
        print_info(f"  - 区域类型: {region.get('region_type')}")
        print_info(f"  - 坐标点数: {len(points)}")
        return True
    else:
        print_error("无法获取区域数据")
        return False

def main():
    """主测试流程"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("="*60)
    print("设备区域检测前后端逻辑流畅性测试")
    print("="*60)
    print(f"{Colors.RESET}\n")
    
    # 测试统计
    passed = 0
    failed = 0
    
    # 测试1: 获取设备列表
    device_id = test_1_get_device_list()
    if device_id:
        passed += 1
    else:
        failed += 1
        print_error("无法继续测试，缺少设备ID")
        return
    
    # 测试2: 抓拍截图
    image_id, image_url = test_2_capture_snapshot(device_id)
    if image_id and image_url:
        passed += 1
    else:
        failed += 1
        print_warning("抓拍失败，但继续测试...")
        image_id = None
    
    # 测试3: 获取区域列表（初始应该为空）
    regions = test_3_get_regions(device_id)
    if regions is not None:
        passed += 1
    else:
        failed += 1
    
    # 测试4: 创建多边形区域
    if image_id:
        region_id_1 = test_4_create_region(device_id, image_id)
        if region_id_1:
            passed += 1
        else:
            failed += 1
    else:
        print_warning("跳过创建区域测试（缺少image_id）")
        region_id_1 = None
    
    # 测试5: 创建线条区域
    if image_id:
        region_id_2 = test_5_create_line_region(device_id, image_id)
        if region_id_2:
            passed += 1
        else:
            failed += 1
    else:
        print_warning("跳过创建线条区域测试（缺少image_id）")
        region_id_2 = None
    
    # 测试6: 更新区域
    if region_id_1:
        if test_6_update_region(region_id_1):
            passed += 1
        else:
            failed += 1
    else:
        print_warning("跳过更新区域测试（缺少region_id）")
    
    # 测试7: 更新封面图
    if test_7_update_cover_image(device_id):
        passed += 1
    else:
        failed += 1
    
    # 测试8: 删除区域
    if region_id_2:
        if test_8_delete_region(region_id_2):
            passed += 1
        else:
            failed += 1
    else:
        print_warning("跳过删除区域测试（缺少region_id）")
    
    # 测试9: 验证数据结构
    if test_9_validate_data_structure(device_id):
        passed += 1
    else:
        failed += 1
    
    # 最终统计
    print_section("测试结果统计")
    total = passed + failed
    print_info(f"总测试数: {total}")
    print_success(f"通过: {passed}")
    if failed > 0:
        print_error(f"失败: {failed}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print_info(f"成功率: {success_rate:.1f}%")
    
    if failed == 0:
        print_success("\n🎉 所有测试通过！前后端逻辑流畅性良好！")
        return 0
    else:
        print_error("\n⚠️  部分测试失败，请检查上述错误信息")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

