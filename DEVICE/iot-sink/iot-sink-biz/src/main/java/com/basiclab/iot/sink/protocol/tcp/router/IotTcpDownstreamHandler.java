package com.basiclab.iot.sink.protocol.tcp.router;

import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.tcp.manager.IotTcpConnectionManager;
import com.basiclab.iot.sink.messagebus.publisher.IotDeviceService;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * IotTcpDownstreamHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@RequiredArgsConstructor
public class IotTcpDownstreamHandler {

    private final IotDeviceMessageService deviceMessageService;

    private final IotDeviceService deviceService;

    private final IotTcpConnectionManager connectionManager;

    /**
     * 处理下行消息
     */
    public void handle(IotDeviceMessage message) {
        try {
            log.info("[handle][处理下行消息，设备 ID: {}，方法: {}，消息 ID: {}]",
                    message.getDeviceId(), message.getMethod(), message.getId());

            // 1.1 获取设备信息
            IotDeviceRespDTO deviceInfo = deviceService.getDeviceFromCache(message.getDeviceId());
            if (deviceInfo == null) {
                log.error("[handle][设备不存在，设备 ID: {}]", message.getDeviceId());
                return;
            }
            // 1.2 检查设备是否在线
            if (connectionManager.isDeviceOffline(message.getDeviceId())) {
                log.warn("[handle][设备不在线，设备 ID: {}]", message.getDeviceId());
                return;
            }

            // 2. 根据产品唯一标识和设备唯一标识编码消息并发送到设备
            byte[] bytes = deviceMessageService.encodeDeviceMessage(message, deviceInfo.getProductIdentification(),
                    deviceInfo.getDeviceIdentification());
            boolean success = connectionManager.sendToDevice(message.getDeviceId(), bytes);
            if (success) {
                log.info("[handle][下行消息发送成功，设备 ID: {}，方法: {}，消息 ID: {}，数据长度: {} 字节]",
                        message.getDeviceId(), message.getMethod(), message.getId(), bytes.length);
            } else {
                log.error("[handle][下行消息发送失败，设备 ID: {}，方法: {}，消息 ID: {}]",
                        message.getDeviceId(), message.getMethod(), message.getId());
            }
        } catch (Exception e) {
            log.error("[handle][处理下行消息失败，设备 ID: {}，方法: {}，消息内容: {}]",
                    message.getDeviceId(), message.getMethod(), message, e);
        }
    }

}