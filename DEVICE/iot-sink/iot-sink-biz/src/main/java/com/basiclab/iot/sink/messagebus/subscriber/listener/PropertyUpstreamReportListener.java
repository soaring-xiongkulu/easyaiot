package com.basiclab.iot.sink.messagebus.subscriber.listener;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.RemoteDeviceService;
import com.basiclab.iot.device.domain.device.vo.PropertyThresholdEvaluateParam;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.service.data.DeviceDataStorageService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.Map;

/**
 * PropertyUpstreamReportListener
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class PropertyUpstreamReportListener {

    @Resource
    private DeviceDataStorageService deviceDataStorageService;

    @Autowired(required = false)
    private RemoteDeviceService remoteDeviceService;

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handlePropertyUpstreamReportEvent(IotMessageBusEvent event) {
        try {
            if (event.getTopicEnum() != IotDeviceTopicEnum.PROPERTY_UPSTREAM_REPORT) {
                return;
            }

            log.debug("[handlePropertyUpstreamReportEvent][处理属性上报上行消息，messageId: {}, topic: {}, deviceId: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), event.getMessage().getDeviceId());

            // 存储数据到TDEngine和Redis
            deviceDataStorageService.storeDeviceData(event.getMessage(), event.getTopicEnum());

            // 阈值评估 → Kafka → iot-message
            evaluateThreshold(event.getMessage());

        } catch (Exception e) {
            log.error("[handlePropertyUpstreamReportEvent][处理属性上报上行消息失败，messageId: {}, topic: {}]",
                    event.getMessage().getId(), event.getMessage().getTopic(), e);
        }
    }

    private void evaluateThreshold(IotDeviceMessage message) {
        if (remoteDeviceService == null || message == null || message.getParams() == null) {
            return;
        }
        try {
            Map<String, Object> properties = toPropertyMap(message.getParams());
            if (properties.isEmpty()) {
                return;
            }
            String deviceIdentification = extractDeviceIdentification(message);
            if (StrUtil.isBlank(deviceIdentification)) {
                return;
            }
            PropertyThresholdEvaluateParam param = new PropertyThresholdEvaluateParam();
            param.setDeviceIdentification(deviceIdentification);
            param.setProperties(properties);
            R<Integer> result = remoteDeviceService.evaluatePropertyThreshold(param);
            if (result != null && result.getData() != null && result.getData() > 0) {
                log.debug("[evaluateThreshold] 触发阈值告警 {} 条 device={}", result.getData(), deviceIdentification);
            }
        } catch (Exception e) {
            log.warn("[evaluateThreshold] 阈值评估失败 messageId={}", message.getId(), e);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> toPropertyMap(Object params) {
        Map<String, Object> result = new HashMap<>();
        if (params instanceof Map) {
            Map<String, Object> map = (Map<String, Object>) params;
            Object nested = map.get("properties");
            if (nested instanceof Map) {
                result.putAll((Map<String, Object>) nested);
            } else {
                result.putAll(map);
            }
            return result;
        }
        try {
            Object parsed = JSONUtil.parse(JSONUtil.toJsonStr(params));
            if (parsed instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> bean = (Map<String, Object>) parsed;
                result.putAll(bean);
            }
        } catch (Exception ignored) {
            // ignore
        }
        return result;
    }

    private String extractDeviceIdentification(IotDeviceMessage message) {
        if (StrUtil.isNotBlank(message.getTopic())) {
            String[] parts = message.getTopic().split("/");
            if (parts.length >= 4 && "iot".equals(parts[1])) {
                return parts[3];
            }
            if (parts.length >= 3) {
                return parts[2];
            }
        }
        return "";
    }
}
