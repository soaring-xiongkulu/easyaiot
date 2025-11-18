package com.basiclab.iot.sink.protocol.emqx.router;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceMessageUtils;
import com.basiclab.iot.sink.protocol.emqx.IotEmqxUpstreamProtocol;
import com.basiclab.iot.sink.messagebus.publisher.IotDeviceService;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.util.IotMqttTopicUtils;
import lombok.extern.slf4j.Slf4j;

/**
 * IotEmqxDownstreamHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public class IotEmqxDownstreamHandler {

    private final IotEmqxUpstreamProtocol protocol;

    private final IotDeviceService deviceService;

    private final IotDeviceMessageService deviceMessageService;

    public IotEmqxDownstreamHandler(IotEmqxUpstreamProtocol protocol) {
        this.protocol = protocol;
        this.deviceService = SpringUtil.getBean(IotDeviceService.class);
        this.deviceMessageService = SpringUtil.getBean(IotDeviceMessageService.class);
    }

    /**
     * 处理下行消息
     *
     * @param message 设备消息
     */
    public void handle(IotDeviceMessage message) {
        // 1. 获取设备信息
        IotDeviceRespDTO deviceInfo = deviceService.getDeviceFromCache(message.getDeviceId());
        if (deviceInfo == null) {
            log.error("[handle][设备信息({})不存在]", message.getDeviceId());
            return;
        }

        // 2.1 根据方法构建主题
        String topic = buildTopicByMethod(message, deviceInfo.getProductIdentification(), deviceInfo.getDeviceIdentification());
        if (StrUtil.isBlank(topic)) {
            log.warn("[handle][未知的消息方法: {}]", message.getMethod());
            return;
        }
        // 2.2 构建载荷
        byte[] payload = deviceMessageService.encodeDeviceMessage(message, deviceInfo.getProductIdentification(),
                deviceInfo.getDeviceIdentification());
        // 2.3 发布消息
        protocol.publishMessage(topic, payload);
    }

    /**
     * 根据消息方法和回复状态构建主题
     *
     * @param message               设备消息
     * @param productIdentification 产品唯一标识
     * @param deviceIdentification  设备唯一标识
     * @return 构建的主题，如果方法不支持返回 null
     */
    private String buildTopicByMethod(IotDeviceMessage message, String productIdentification, String deviceIdentification) {
        // 1. 判断是否为回复消息
        boolean isReply = IotDeviceMessageUtils.isReplyMessage(message);
        // 2. 根据消息方法类型构建对应的主题
        return IotMqttTopicUtils.buildTopicByMethod(message.getMethod(), productIdentification, deviceIdentification, isReply);
    }

}