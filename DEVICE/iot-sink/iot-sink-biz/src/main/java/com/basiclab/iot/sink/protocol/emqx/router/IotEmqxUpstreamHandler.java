package com.basiclab.iot.sink.protocol.emqx.router;

import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.core.util.TenantUtils;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.biz.dto.IotDeviceRespDTO;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.emqx.IotEmqxUpstreamProtocol;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import com.basiclab.iot.sink.service.device.DeviceService;
import io.vertx.mqtt.messages.MqttPublishMessage;
import lombok.extern.slf4j.Slf4j;

import java.nio.charset.StandardCharsets;

/**
 * IotEmqxUpstreamHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
public class IotEmqxUpstreamHandler {

    private final IotDeviceMessageService deviceMessageService;
    private final DeviceService deviceService;

    private final String serverId;

    private final IotAlgoBusMqttHandler algoBusMqttHandler;

    public IotEmqxUpstreamHandler(IotEmqxUpstreamProtocol protocol) {
        this.deviceMessageService = SpringUtil.getBean(IotDeviceMessageService.class);
        this.deviceService = SpringUtil.getBean(DeviceService.class);
        this.serverId = protocol.getServerId();
        this.algoBusMqttHandler = new IotAlgoBusMqttHandler();
    }

    /**
     * 处理 MQTT 发布消息
     */
    public void handle(MqttPublishMessage mqttMessage) {
        log.debug("[handle][收到 MQTT 消息, topic: {}, payloadLen: {}]",
                mqttMessage.topicName(),
                mqttMessage.payload() != null ? mqttMessage.payload().length() : 0);
        String topic = mqttMessage.topicName();
        byte[] payload = mqttMessage.payload().getBytes();
        try {
            // 算法总线 Topic：独立入库链路（带边缘节点维度）
            if (algoBusMqttHandler.supports(topic)) {
                algoBusMqttHandler.handle(topic, payload);
                return;
            }

            // 1. 解析主题
            String[] topicParts = topic.split("/");
            if (topicParts.length < 4 || StrUtil.hasBlank(topicParts[2], topicParts[3])) {
                log.warn("[handle][topic({}) 格式不正确，无法解析 productIdentification / deviceIdentification]", topic);
                return;
            }

            String productIdentification = topicParts[2];
            String deviceIdentification = topicParts[3];

            // 2. 解析租户：标准 JSON 取 tenantId；私有协议则按设备表反查
            Long tenantId = resolveTenantId(payload, productIdentification, deviceIdentification);
            if (tenantId == null) {
                log.warn("[handle][topic({}) 无法解析 tenantId：payload 非标准 JSON 且设备不存在 {}/{}]",
                        topic, productIdentification, deviceIdentification);
                return;
            }

            // 3. 解码并投递（脚本 rawDataToProtocol → Codec）
            TenantUtils.execute(tenantId, () -> {
                IotDeviceMessage message = deviceMessageService.decodeDeviceMessageByTopic(payload, topic);
                if (message == null) {
                    log.warn("[handle][topic({}) 消息解码失败，payloadHex={}]",
                            topic, toHexPreview(payload));
                    return;
                }

                if (message.getTenantId() != null && !tenantId.equals(message.getTenantId())) {
                    throw new IllegalArgumentException("tenantId changed while decoding MQTT message");
                }
                message.setTenantId(tenantId);
                deviceMessageService.sendDeviceMessage(
                        message, productIdentification, deviceIdentification, serverId);
            });
        } catch (Exception e) {
            log.error("[handle][topic({}) 处理异常 payloadHex={}]", topic, toHexPreview(payload), e);
        }
    }

    /**
     * 租户解析顺序：
     * 1) 标准 JSON 消息体 tenantId
     * 2) 紧凑文本协议 EA|UP|&lt;tenantId&gt;|...
     * 3) 按 product/device 查库（私有二进制协议）
     */
    private Long resolveTenantId(byte[] payload, String productIdentification, String deviceIdentification) {
        // 1. JSON
        try {
            IotDeviceMessage envelope = JsonUtils.parseObject(payload, IotDeviceMessage.class);
            if (envelope != null && envelope.getTenantId() != null) {
                return envelope.getTenantId();
            }
        } catch (Exception ignored) {
            // 私有协议非 JSON，继续
        }

        // 2. EA|UP|<tenantId>|...
        try {
            String text = new String(payload, StandardCharsets.UTF_8);
            if (text.startsWith("EA|UP|")) {
                String[] parts = text.split("\\|", 5);
                if (parts.length >= 3 && StrUtil.isNotBlank(parts[2])) {
                    return Long.parseLong(parts[2].trim());
                }
            }
        } catch (Exception ignored) {
            // ignore
        }

        // 3. 设备表
        IotDeviceRespDTO device = deviceService.getDeviceIgnoreTenant(productIdentification, deviceIdentification);
        return device != null ? device.getTenantId() : null;
    }

    private static String toHexPreview(byte[] payload) {
        if (payload == null || payload.length == 0) {
            return "";
        }
        int n = Math.min(payload.length, 64);
        StringBuilder sb = new StringBuilder(n * 2);
        for (int i = 0; i < n; i++) {
            sb.append(String.format("%02x", payload[i] & 0xFF));
        }
        if (payload.length > n) {
            sb.append("...");
        }
        return sb.toString();
    }
}
