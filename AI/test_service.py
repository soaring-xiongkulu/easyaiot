#!/usr/bin/env python3
"""
测试 services 服务启动脚本
用于验证模型部署服务是否能正常启动和运行
"""
import os
import sys
import time
import signal
import subprocess
import requests
import socket
from pathlib import Path


class ServiceTester:
    """服务测试类"""
    
    def __init__(self, model_path=None, port=8000, service_name="test_deploy_service"):
        """
        初始化测试器
        
        Args:
            model_path: 模型文件路径，如果为None则自动查找
            port: 服务端口，默认8000
            service_name: 服务名称，默认test_deploy_service
        """
        self.port = port
        self.service_name = service_name
        self.process = None
        self.base_url = f"http://localhost:{port}"
        
        # 自动查找模型文件
        if model_path is None:
            model_path = self._find_model_file()
        
        self.model_path = model_path
        if not self.model_path:
            raise ValueError("未找到模型文件，请指定 MODEL_PATH 环境变量或确保 AI 目录下有 .pt 或 .onnx 文件")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        print(f"📦 使用模型文件: {self.model_path}")
        print(f"🌐 服务地址: {self.base_url}")
        print(f"🔧 服务名称: {self.service_name}")
    
    def _find_model_file(self):
        """自动查找模型文件"""
        # 获取 AI 目录路径
        ai_dir = Path(__file__).parent.absolute()
        
        # 查找 .pt 文件
        pt_files = list(ai_dir.glob("*.pt"))
        if pt_files:
            return str(pt_files[0])
        
        # 查找 .onnx 文件
        onnx_files = list(ai_dir.glob("*.onnx"))
        if onnx_files:
            return str(onnx_files[0])
        
        # 查找 services 目录下的模型文件
        services_dir = ai_dir / "services"
        if services_dir.exists():
            pt_files = list(services_dir.glob("*.pt"))
            if pt_files:
                return str(pt_files[0])
            
            onnx_files = list(services_dir.glob("*.onnx"))
            if onnx_files:
                return str(onnx_files[0])
        
        return None
    
    def _is_port_available(self, port):
        """检查端口是否可用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except OSError:
                return False
    
    def _wait_for_service(self, timeout=60):
        """等待服务启动"""
        print(f"⏳ 等待服务启动（最多等待 {timeout} 秒）...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查进程是否还在运行
            if self.process and self.process.poll() is not None:
                print(f"❌ 服务进程已退出，退出码: {self.process.returncode}")
                # 尝试读取剩余输出
                if self.process.stdout:
                    try:
                        remaining_output = self.process.stdout.read()
                        if remaining_output:
                            print(f"[服务] {remaining_output.decode('utf-8', errors='ignore')}")
                    except:
                        pass
                if self.process.stderr:
                    try:
                        remaining_error = self.process.stderr.read()
                        if remaining_error:
                            print(f"[服务] {remaining_error.decode('utf-8', errors='ignore')}")
                    except:
                        pass
                return False
            
            # 检查端口是否在监听（简化逻辑：只要端口打开就认为服务已启动）
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', self.port))
                    if result == 0:
                        # 端口已打开，认为服务已启动（不再进行健康检查）
                        print("✅ 服务已启动（端口已打开）")
                        return True
            except Exception:
                pass
            
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"   等待中... ({elapsed}/{timeout} 秒)")
        
        print("❌ 服务启动超时")
        # 检查端口是否在监听
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', self.port))
                if result == 0:
                    print(f"⚠️  端口 {self.port} 已打开，但启动检测超时")
                else:
                    print(f"⚠️  端口 {self.port} 未打开")
        except Exception as e:
            print(f"⚠️  检查端口时出错: {str(e)}")
        return False
    
    def _read_output(self, pipe, prefix="[服务]"):
        """读取进程输出并实时显示"""
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    line_str = line.rstrip()
                    if line_str:
                        print(f"{prefix} {line_str}")
        except Exception as e:
            print(f"⚠️  读取输出时出错: {str(e)}")
        finally:
            pipe.close()
    
    def start_service(self):
        """启动服务"""
        # 检查端口是否被占用
        if not self._is_port_available(self.port):
            print(f"⚠️  端口 {self.port} 已被占用，尝试使用其他端口...")
            # 尝试找到可用端口
            for p in range(self.port, self.port + 10):
                if self._is_port_available(p):
                    self.port = p
                    self.base_url = f"http://localhost:{p}"
                    print(f"✅ 使用端口: {p}")
                    break
            else:
                raise RuntimeError(f"无法找到可用端口（从 {self.port} 开始）")
        
        # 设置环境变量
        env = os.environ.copy()
        env['SERVICE_NAME'] = self.service_name
        env['MODEL_PATH'] = self.model_path
        env['PORT'] = str(self.port)
        env['MODEL_FORMAT'] = 'pytorch' if self.model_path.endswith('.pt') else 'onnx'
        env['PYTHONUNBUFFERED'] = '1'
        
        # 可选：设置其他环境变量（如果存在）
        if 'MODEL_ID' not in env:
            env['MODEL_ID'] = 'test_model'
        if 'MODEL_VERSION' not in env:
            env['MODEL_VERSION'] = 'V1.0.0'
        
        # 获取 services 目录路径
        services_dir = Path(__file__).parent.absolute() / "services"
        run_deploy_path = services_dir / "run_deploy.py"
        
        if not run_deploy_path.exists():
            raise FileNotFoundError(f"找不到服务启动脚本: {run_deploy_path}")
        
        print(f"🚀 启动服务...")
        print(f"   脚本路径: {run_deploy_path}")
        print(f"   模型路径: {self.model_path}")
        print(f"   端口: {self.port}")
        
        # 启动服务进程
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(run_deploy_path)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(services_dir),
                text=True,  # 使用文本模式
                bufsize=1  # 行缓冲
            )
            
            # 启动线程实时读取输出
            import threading
            stdout_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stdout, "[服务]"),
                daemon=True
            )
            stderr_thread = threading.Thread(
                target=self._read_output,
                args=(self.process.stderr, "[服务]"),
                daemon=True
            )
            stdout_thread.start()
            stderr_thread.start()
            
            # 等待服务启动，使用更长的等待时间和重试机制
            print("⏳ 等待服务启动...")
            max_wait_time = 30  # 最多等待30秒
            check_interval = 2  # 每2秒检查一次
            waited_time = 0
            
            while waited_time < max_wait_time:
                # 检查进程是否还在运行
                if self.process.poll() is not None:
                    # 进程已经退出，读取剩余输出
                    print("❌ 服务进程已退出")
                    # 等待输出线程完成
                    time.sleep(0.5)
                    return False
                
                # 检查端口是否打开
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(1)
                        result = s.connect_ex(('localhost', self.port))
                        if result == 0:
                            # 端口已打开，再等待1秒确保Flask完全启动
                            time.sleep(1)
                            print(f"✅ 服务已启动（端口 {self.port} 已打开）")
                            return True
                except Exception:
                    pass
                
                time.sleep(check_interval)
                waited_time += check_interval
                if waited_time % 6 == 0:  # 每6秒打印一次进度
                    print(f"   等待中... ({waited_time}/{max_wait_time} 秒)")
            
            # 如果超时，检查进程是否还在运行
            if self.process.poll() is None:
                print(f"⚠️  等待超时，但服务进程仍在运行")
                print("💡 提示：如果服务已注册到 Nacos，说明服务可能已启动，但端口检查失败")
                print("💡 提示：可能是服务绑定到了其他IP地址，而不是localhost")
                return True  # 进程还在运行，认为启动成功
            else:
                print("❌ 服务进程已退出")
                return False
                
        except Exception as e:
            print(f"❌ 启动服务失败: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.process:
                self.stop_service()
            return False
    
    def test_health(self):
        """测试健康检查接口"""
        print("\n" + "="*60)
        print("📊 测试健康检查接口")
        print("="*60)
        
        # 重试机制：最多重试5次，每次间隔2秒
        max_retries = 5
        retry_interval = 2
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"响应数据: {data}")
                    
                    if data.get('status') == 'healthy':
                        print("✅ 健康检查通过")
                        return True
                    else:
                        print(f"⚠️  服务状态异常: {data.get('status')}")
                        return False
                else:
                    print(f"❌ 健康检查失败，状态码: {response.status_code}")
                    print(f"响应内容: {response.text}")
                    if attempt < max_retries:
                        print(f"   重试中... ({attempt}/{max_retries})")
                        time.sleep(retry_interval)
                        continue
                    return False
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ 健康检查请求失败: {str(e)}")
                if attempt < max_retries:
                    print(f"   重试中... ({attempt}/{max_retries})")
                    time.sleep(retry_interval)
                    continue
                else:
                    print(f"⚠️  已重试 {max_retries} 次，仍然失败")
                    print("💡 提示：如果服务已注册到 Nacos，可能是服务绑定到了其他IP地址")
                    return False
        
        return False
    
    def test_stop(self):
        """测试停止服务接口"""
        print("\n" + "="*60)
        print("🛑 测试停止服务接口")
        print("="*60)
        
        try:
            response = requests.post(f"{self.base_url}/stop", timeout=5)
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据: {data}")
                
                if data.get('code') == 0:
                    print("✅ 停止服务请求成功")
                    # 等待服务停止
                    time.sleep(2)
                    return True
                else:
                    print(f"⚠️  停止服务返回异常: {data.get('msg')}")
                    return False
            else:
                print(f"❌ 停止服务失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 停止服务请求失败: {str(e)}")
            return False
    
    def stop_service(self):
        """停止服务进程"""
        if self.process:
            print("\n" + "="*60)
            print("🛑 停止服务进程")
            print("="*60)
            
            try:
                # 先尝试优雅停止
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    print("✅ 服务已停止")
                except subprocess.TimeoutExpired:
                    # 如果5秒内没有停止，强制终止
                    print("⚠️  服务未在5秒内停止，强制终止...")
                    self.process.kill()
                    self.process.wait()
                    print("✅ 服务已强制停止")
            except Exception as e:
                print(f"⚠️  停止服务时出错: {str(e)}")
            
            self.process = None
    
    def run_all_tests(self):
        """运行所有测试"""
        print("="*60)
        print("🧪 Services 服务测试")
        print("="*60)
        
        results = {}
        
        try:
            # 启动服务
            if not self.start_service():
                print("\n❌ 服务启动失败，无法继续测试")
                return False
            
            # 测试健康检查
            results['health'] = self.test_health()
            
            # 注意：不测试 stop 接口，因为测试后服务会停止
            # 如果需要测试 stop 接口，可以取消下面的注释
            # results['stop'] = self.test_stop()
            
            # 打印测试结果
            print("\n" + "="*60)
            print("📋 测试结果汇总")
            print("="*60)
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                print(f"{test_name}: {status}")
            
            all_passed = all(results.values())
            if all_passed:
                print("\n🎉 所有测试通过！")
            else:
                print("\n⚠️  部分测试失败")
            
            return all_passed
            
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被用户中断")
            return False
        except Exception as e:
            print(f"\n❌ 测试过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 清理资源
            self.stop_service()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='测试 services 服务启动')
    parser.add_argument('--model-path', type=str, default=None,
                        help='模型文件路径（如果不指定，会自动查找）')
    parser.add_argument('--port', type=int, default=8000,
                        help='服务端口（默认: 8000）')
    parser.add_argument('--service-name', type=str, default='test_deploy_service',
                        help='服务名称（默认: test_deploy_service）')
    
    args = parser.parse_args()
    
    try:
        tester = ServiceTester(
            model_path=args.model_path,
            port=args.port,
            service_name=args.service_name
        )
        
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ 初始化测试器失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

