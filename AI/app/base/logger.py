import logging
import sys

from app.config import config


def init_logger():
    from app.base.mqtt import get_mqtt_service, on_connected
    class ReportMQTTHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self._message_cache = []  # 当mqtt没有connected时，report一定失败，这样会漏日志，所以做个缓存
            @on_connected
            def report_cache():
                mqtt_service = get_mqtt_service()
                for log in self._message_cache:
                    mqtt_service.report_syslog(log)
                self._message_cache.clear()
    
        def emit(self, record):
            msg = self.format(record)
            mqtt_service = get_mqtt_service()
            if not mqtt_service.enbale:
                return
            if mqtt_service.connected and not self._message_cache:  # 保证日志的顺序，不然刚连接上的那条日志肯定是发送最快的
                mqtt_service.report_syslog(msg)
            else:
                self._message_cache.append(msg)
                
    logger = logging.getLogger('easyaiot')
    logger.setLevel(config._LOGGER_LEVEL)

    # 加mqtthandler
    mqtt_hdlr = ReportMQTTHandler()
    mqtt_hdlr.setFormatter(logging.Formatter('[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s'))
    logger.addHandler(mqtt_hdlr)
    
    # 加输出handler
    output_hdlr = logging.StreamHandler(sys.stdout)
    output_hdlr.setFormatter(logging.Formatter('[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s'))
    logger.addHandler(output_hdlr)

# 用这个获取不同模块的日志器，子模块用.分割
def get_logger(module_name: str):
    logger = logging.getLogger(f'easyaiot.{module_name}')
    return logger
