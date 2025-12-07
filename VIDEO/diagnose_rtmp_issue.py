#!/usr/bin/env python3
"""
RTMP推流问题诊断工具
检查SRS服务器、回调服务和网络连接
"""
import subprocess
import requests
import socket
import sys
from pathlib import Path

def check_port(host, port, timeout=2):
    """检查端口是否可访问"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_http_endpoint(url, timeout=2):
    """检查HTTP端点是否可访问"""
    try:
        response = requests.post(
            url,
            json={"action": "on_publish", "test": True},
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code == 200
    except Exception:
        return False

def get_docker_gateway_ip(container_name="srs-server"):
    """获取Docker容器的网关IP"""
    try:
        result = subprocess.run(
            ["docker", "inspect", container_name, "--format", 
             "{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            ip = result.stdout.strip()
            if ip:
                return ip
    except Exception:
        pass
    return None

def check_srs_status():
    """检查SRS服务状态"""
    print("\n" + "=" * 60)
    print("📡 检查SRS服务")
    print("=" * 60)
    
    # 检查Docker容器
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=srs", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "srs" in result.stdout.lower():
            print("✅ SRS容器正在运行")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ SRS容器未运行")
            print("   💡 启动命令: docker start srs-server")
            return False
    except Exception as e:
        print(f"⚠️  无法检查Docker容器: {str(e)}")
    
    # 检查端口
    ports_to_check = [
        (1935, "RTMP推流端口"),
        (1985, "HTTP API端口"),
        (8080, "HTTP服务器端口"),
    ]
    
    all_ok = True
    for port, desc in ports_to_check:
        if check_port("localhost", port):
            print(f"✅ {desc} (localhost:{port}) 可访问")
        else:
            print(f"❌ {desc} (localhost:{port}) 不可访问")
            all_ok = False
    
    return all_ok

def check_callback_endpoints():
    """检查回调端点"""
    print("\n" + "=" * 60)
    print("🔗 检查回调端点")
    print("=" * 60)
    
    # 获取Docker网关IP
    gateway_ip = get_docker_gateway_ip()
    if gateway_ip:
        print(f"📌 Docker网关IP: {gateway_ip}")
    else:
        gateway_ip = "172.18.0.1"
        print(f"📌 使用默认网关IP: {gateway_ip}")
    
    # 检查的端点列表
    endpoints = [
        (f"http://{gateway_ip}:48080/admin-api/video/camera/callback/on_publish", 
         "通过网关访问 (SRS配置的地址)"),
        ("http://localhost:48080/admin-api/video/camera/callback/on_publish",
         "通过localhost访问网关"),
        ("http://localhost:6000/camera/callback/on_publish",
         "直接访问VIDEO服务"),
    ]
    
    accessible = []
    for url, desc in endpoints:
        print(f"\n🔍 {desc}")
        print(f"   URL: {url}")
        if check_http_endpoint(url):
            print("   ✅ 可访问")
            accessible.append(url)
        else:
            print("   ❌ 不可访问")
    
    return accessible

def check_video_service():
    """检查VIDEO服务"""
    print("\n" + "=" * 60)
    print("🎥 检查VIDEO服务")
    print("=" * 60)
    
    # 检查进程
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "run.py" in result.stdout or "flask" in result.stdout.lower():
            print("✅ VIDEO服务进程正在运行")
            for line in result.stdout.split('\n'):
                if "run.py" in line or ("flask" in line.lower() and "python" in line.lower()):
                    parts = line.split()
                    if len(parts) > 1:
                        print(f"   PID: {parts[1]}, 命令: {' '.join(parts[10:13])}")
        else:
            print("❌ VIDEO服务进程未运行")
            print("   💡 启动命令: cd VIDEO && python run.py")
            return False
    except Exception as e:
        print(f"⚠️  无法检查进程: {str(e)}")
    
    # 检查端口
    if check_port("localhost", 6000):
        print("✅ VIDEO服务端口 (localhost:6000) 可访问")
        return True
    else:
        print("❌ VIDEO服务端口 (localhost:6000) 不可访问")
        return False

def check_gateway_service():
    """检查网关服务"""
    print("\n" + "=" * 60)
    print("🚪 检查网关服务")
    print("=" * 60)
    
    # 检查端口
    if check_port("localhost", 48080):
        print("✅ 网关服务端口 (localhost:48080) 可访问")
        return True
    else:
        print("❌ 网关服务端口 (localhost:48080) 不可访问")
        print("   💡 网关服务可能未启动")
        print("   💡 检查命令: docker ps | grep gateway 或检查DEVICE服务")
        return False

def provide_solutions(has_srs, has_video, has_gateway, accessible_endpoints):
    """提供解决方案"""
    print("\n" + "=" * 60)
    print("💡 解决方案")
    print("=" * 60)
    
    if not has_srs:
        print("\n1️⃣ 启动SRS服务:")
        print("   docker start srs-server")
        print("   或检查SRS容器状态: docker ps | grep srs")
        return
    
    if not has_video and not has_gateway:
        print("\n⚠️  VIDEO服务和网关服务都未运行")
        print("\n选项1: 启动VIDEO服务（推荐用于测试）")
        print("   cd /opt/projects/easyaiot/VIDEO")
        print("   python run.py")
        print("\n选项2: 启动网关服务")
        print("   检查DEVICE服务是否运行")
        print("\n选项3: 使用临时mock回调服务器（仅用于测试）")
        print("   python mock_callback_server.py")
        return
    
    if not accessible_endpoints:
        print("\n⚠️  所有回调端点都不可访问")
        print("\n解决方案:")
        if not has_video:
            print("1. 启动VIDEO服务:")
            print("   cd /opt/projects/easyaiot/VIDEO")
            print("   python run.py")
        if not has_gateway:
            print("2. 启动网关服务（如果使用网关）")
        print("\n3. 或者使用临时mock回调服务器:")
        print("   python mock_callback_server.py")
        print("   然后更新SRS配置指向mock服务器")
    else:
        print(f"\n✅ 找到 {len(accessible_endpoints)} 个可访问的回调端点")
        print("   如果SRS配置的回调地址不可访问，请:")
        print("   1. 检查SRS配置文件中的回调URL")
        print("   2. 确保回调URL与可访问的端点一致")
        if accessible_endpoints:
            print("\n   可用的回调端点:")
            for url in accessible_endpoints:
                print(f"   - {url}")

def main():
    print("=" * 60)
    print("🔍 RTMP推流问题诊断工具")
    print("=" * 60)
    
    # 检查各项服务
    has_srs = check_srs_status()
    has_video = check_video_service()
    has_gateway = check_gateway_service()
    accessible_endpoints = check_callback_endpoints()
    
    # 提供解决方案
    provide_solutions(has_srs, has_video, has_gateway, accessible_endpoints)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

