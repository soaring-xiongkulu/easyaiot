#!/usr/bin/env python3
"""兼容入口：历史安装脚本与 systemd 仍调用 run_agent.py。"""
from run_sentinel import main

if __name__ == '__main__':
    main()
