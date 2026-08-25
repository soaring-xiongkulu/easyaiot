#!/usr/bin/env python3
"""SRS hook mock: 响应 on_publish / on_dvr 等回调，返回 code=0 使 SRS 接受推流

注意：监听端口固定为 48081，不要改回 48080！
48080 是 iot-gateway 的端口（SRS hook 生产配置指向 172.18.0.1:48080 经网关转发），
若占用会导致网关启动失败、管理后台全部接口不可用。

用法：
    python3 mock_srs_hook_server.py [--port 48081]
"""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

DEFAULT_PORT = 48081  # 勿改为 48080，见文件头注释

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else b''
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}
        action = data.get('action', self.path)
        print(f'[hook] {self.path} action={action}', flush=True)
        resp = json.dumps({'code': 0}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def do_GET(self):
        resp = b'Mock SRS hook server is running'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, fmt, *args):
        pass

def main():
    parser = argparse.ArgumentParser(description='SRS hook mock 服务器')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'监听端口 (默认: {DEFAULT_PORT}，勿使用 48080)')
    args = parser.parse_args()
    print(f'SRS hook mock listening on 0.0.0.0:{args.port}')
    HTTPServer(('0.0.0.0', args.port), Handler).serve_forever()

if __name__ == '__main__':
    main()
