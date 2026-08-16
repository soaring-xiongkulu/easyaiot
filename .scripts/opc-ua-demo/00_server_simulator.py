#!/usr/bin/env python3
"""OPC UA 演示服务器（依赖 asyncua）。提供 Temperature / Setpoint / Running 节点。"""

from __future__ import annotations

import argparse
import asyncio
import sys

try:
    from asyncua import Server, ua
except ImportError as exc:  # pragma: no cover
    raise SystemExit("请先安装: pip install asyncua") from exc


async def main() -> None:
    parser = argparse.ArgumentParser(description="OPC UA demo server")
    parser.add_argument("--endpoint", default="opc.tcp://0.0.0.0:4840/freeopcua/server/")
    args = parser.parse_args()

    server = Server()
    await server.init()
    server.set_endpoint(args.endpoint)
    server.set_server_name("EasyAIoT OPC UA Demo")
    # 仅开放无安全端点，避免缺证书时跳过全部加密策略、启动异常或客户端连不上
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    uri = "http://easyaiot.local/opcua/demo"
    idx = await server.register_namespace(uri)
    objects = server.get_objects_node()

    # 显式使用字符串 NodeId，避免新版 asyncua 默认生成 ns=x;i=N 导致平台配置对不上
    device = await objects.add_object(ua.NodeId("DemoDevice", idx), ua.QualifiedName("DemoDevice", idx))
    temperature = await device.add_variable(
        ua.NodeId("Temperature", idx), ua.QualifiedName("Temperature", idx), 25.0
    )
    setpoint = await device.add_variable(
        ua.NodeId("Setpoint", idx), ua.QualifiedName("Setpoint", idx), 20.0
    )
    running = await device.add_variable(
        ua.NodeId("Running", idx), ua.QualifiedName("Running", idx), False
    )
    await temperature.set_writable()
    await setpoint.set_writable()
    await running.set_writable()

    print(f"OPC UA server: {args.endpoint}", flush=True)
    print(
        f"NodeIds: ns={idx};s=Temperature | ns={idx};s=Setpoint | ns={idx};s=Running",
        flush=True,
    )
    print("SecurityPolicy=None / Anonymous 即可连接", flush=True)

    async with server:
        # 进入 context 后才真正 bind 监听；供 start 脚本探测就绪
        print("OPC UA READY", flush=True)
        value = 25.0
        while True:
            value += 0.5
            if value > 40:
                value = 20.0
            await temperature.write_value(value)
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:  # pragma: no cover
        print(f"OPC UA server fatal: {exc}", file=sys.stderr, flush=True)
        raise
