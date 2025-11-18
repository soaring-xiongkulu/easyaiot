package com.basiclab.iot.sink.codec.topic;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.codec.IotDeviceMessageCodec;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * IotTopicDeviceMessageCodec
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class IotTopicDeviceMessageCodec implements IotDeviceMessageCodec {

    /**
     * 支持的 Topic 模式（通配符模式，匹配所有标准 IoT Topic）
     */
    private static final String TOPIC_PATTERN = "/iot/${productIdentification}/${deviceIdentification}/#";

    @Override
    public byte[] encode(IotDeviceMessage message) {
        try {
            // 使用 JSON 格式编码
            return JsonUtils.toJsonByte(message);
        } catch (Exception e) {
            log.error("[encode][编码消息失败，messageId: {}]", message.getId(), e);
            throw new RuntimeException("编码消息失败", e);
        }
    }

    @Override
    public IotDeviceMessage decode(byte[] bytes) {
        try {
            // 使用 JSON 格式解码
            return JsonUtils.parseObject(bytes, IotDeviceMessage.class);
        } catch (Exception e) {
            log.error("[decode][解码消息失败]", e);
            throw new RuntimeException("解码消息失败", e);
        }
    }

    @Override
    public String topic() {
        return TOPIC_PATTERN;
    }

    @Override
    public boolean supports(String topic) {
        if (topic == null || topic.isEmpty()) {
            return false;
        }
        // 匹配所有以 /iot/ 开头的 topic
        if (topic.startsWith("/iot/")) {
            return true;
        }
        // 匹配其他标准 topic
        if (topic.startsWith("/shadow/") || 
            topic.startsWith("/ext/") || 
            topic.startsWith("/broadcast/") || 
            topic.startsWith("/ota/")) {
            return true;
        }
        return false;
    }
}

