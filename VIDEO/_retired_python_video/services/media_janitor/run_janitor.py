#!/usr/bin/env python3
"""媒体 Janitor 独立进程：周期扫描孤儿 DVR/抓拍文件。"""
import logging
import os
import sys
import time

VIDEO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if VIDEO_ROOT not in sys.path:
    sys.path.insert(0, VIDEO_ROOT)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger('media-janitor')

INTERVAL = int(os.getenv('JANITOR_INTERVAL_SECONDS', '60'))


def run():
    from run import create_app
    from app.services.media_janitor_service import is_janitor_enabled, run_janitor_cycle

    if not is_janitor_enabled():
        logger.info('Janitor 已关闭 (MEDIA_JANITOR_ENABLED=false)')
        return

    app = create_app(start_background_tasks=False)
    logger.info('Janitor 启动，间隔 %ss', INTERVAL)
    with app.app_context():
        while True:
            try:
                run_janitor_cycle()
            except Exception as e:
                logger.error('Janitor 周期异常: %s', e, exc_info=True)
            time.sleep(INTERVAL)


if __name__ == '__main__':
    run()
