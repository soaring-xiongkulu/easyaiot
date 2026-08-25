#!/usr/bin/env python3
"""
临时Mock回调服务器
用于测试RTMP推流，当VIDEO服务或网关服务未运行时
此服务器会快速响应SRS的回调请求，允许推流

注意：默认端口为 48081，不要使用 48080！
48080 是 iot-gateway 的端口，占用会导致网关启动失败、管理后台全部接口不可用。
"""
import http.server
import socketserver
import json
import sys
from urllib.parse import urlparse, parse_qs

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    """处理SRS回调请求"""
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # 解析JSON
            try:
                data = json.loads(body.decode('utf-8'))
            except:
                data = {}
            
            # 记录请求信息
            action = data.get('action', 'unknown')
            stream = data.get('stream', 'unknown')
            client_id = data.get('client_id', 'unknown')
            
            print(f"📥 收到回调: action={action}, stream={stream}, client_id={client_id}")
            
            # 返回允许推流的响应
            response = {
                'code': 0,
                'msg': None
            }
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
            print(f"✅ 已允许推流: stream={stream}")
            
        except Exception as e:
            print(f"❌ 处理回调时出错: {str(e)}")
            # 即使出错也返回允许，避免阻塞推流
            response = {'code': 0, 'msg': None}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_GET(self):
        """处理GET请求（健康检查）"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Mock Callback Server is running')
    
    def log_message(self, format, *args):
        """重写日志方法，使用print而不是stderr"""
        pass  # 使用print输出，不记录HTTP访问日志

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='临时Mock回调服务器，用于测试RTMP推流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用说明:
  1. 启动mock服务器:
     python mock_callback_server.py --port 48081 --path /admin-api/video/camera/callback/on_publish
  
  2. 如果SRS配置的回调地址是 http://172.18.0.1:48080/admin-api/video/camera/callback/on_publish
     需要确保172.18.0.1可以访问到运行mock服务器的机器
  
  3. 或者修改SRS配置指向mock服务器地址
  
  4. 注意: 这只是临时测试方案，生产环境应使用真实的VIDEO服务
  5. 重要: 默认端口是 48081，勿用 48080（iot-gateway 专用，占用会导致网关无法启动）
        """
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='监听地址 (默认: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=48081,
        help='监听端口 (默认: 48081；勿用48080，那是iot-gateway的端口)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Mock回调服务器")
    print("=" * 60)
    print(f"📡 监听地址: {args.host}:{args.port}")
    print(f"🔗 回调端点: http://{args.host}:{args.port}/<path>")
    print("\n💡 说明:")
    print("   - 此服务器会快速响应所有回调请求，允许推流")
    print("   - 仅用于测试，生产环境请使用真实的VIDEO服务")
    print("   - 按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    try:
        with socketserver.TCPServer((args.host, args.port), CallbackHandler) as httpd:
            print(f"✅ 服务器已启动: http://{args.host}:{args.port}")
            print("   等待回调请求...\n")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ 错误: 端口 {args.port} 已被占用")
            print(f"💡 请使用其他端口: python mock_callback_server.py --port <其他端口>")
        else:
            print(f"❌ 启动失败: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 收到停止信号，正在关闭服务器...")
        sys.exit(0)

if __name__ == "__main__":
    main()

