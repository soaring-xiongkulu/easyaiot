#!/usr/bin/env python3
"""
测试SRS回调服务是否可访问
"""
import requests
import sys
import json

def test_callback_service():
    """测试回调服务是否可访问"""
    # 测试不同的回调URL
    callback_urls = [
        "http://localhost:6000/callback/on_publish",  # 直接访问VIDEO服务
        "http://127.0.0.1:6000/callback/on_publish",
        "http://172.18.0.1:48080/admin-api/video/camera/callback/on_publish",  # 通过网关访问
        "http://localhost:48080/admin-api/video/camera/callback/on_publish",
    ]
    
    # 模拟SRS回调数据
    test_data = {
        "action": "on_publish",
        "client_id": "test-client-123",
        "ip": "127.0.0.1",
        "vhost": "__defaultVhost__",
        "app": "live",
        "stream": "1764341204704370850",
        "stream_url": "/live/1764341204704370850",
        "param": ""
    }
    
    print("=" * 60)
    print("🔍 测试SRS回调服务可访问性")
    print("=" * 60)
    
    success_count = 0
    for url in callback_urls:
        print(f"\n📡 测试URL: {url}")
        try:
            response = requests.post(
                url,
                json=test_data,
                timeout=2,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print(f"   ✅ 成功 - 响应: {json.dumps(result)}")
                    success_count += 1
                else:
                    print(f"   ⚠️  响应码非0 - 响应: {json.dumps(result)}")
            else:
                print(f"   ❌ HTTP错误 - 状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:200]}")
        except requests.exceptions.Timeout:
            print(f"   ❌ 超时 - 无法在2秒内连接")
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ 连接错误 - {str(e)}")
        except Exception as e:
            print(f"   ❌ 其他错误 - {str(e)}")
    
    print("\n" + "=" * 60)
    if success_count > 0:
        print(f"✅ 测试完成: {success_count}/{len(callback_urls)} 个URL可访问")
        print("\n💡 建议:")
        print("   1. 如果直接访问VIDEO服务(6000端口)成功，但通过网关(48080端口)失败，")
        print("      请检查网关服务是否运行")
        print("   2. 如果所有URL都失败，请检查VIDEO服务是否正常运行")
        print("   3. 确保SRS配置中的回调URL与可访问的URL一致")
    else:
        print(f"❌ 测试完成: 所有URL都无法访问")
        print("\n💡 请检查:")
        print("   1. VIDEO服务是否运行: ps aux | grep run.py")
        print("   2. 端口是否监听: netstat -tuln | grep 6000")
        print("   3. 防火墙设置")
    print("=" * 60)

if __name__ == "__main__":
    test_callback_service()

