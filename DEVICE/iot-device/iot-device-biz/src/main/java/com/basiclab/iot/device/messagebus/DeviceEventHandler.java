package com.basiclab.iot.device.messagebus;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.device.domain.device.vo.DeviceEvent;
import com.basiclab.iot.device.service.device.DeviceEventService;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * DeviceEventHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
@Transactional(rollbackFor = Exception.class)
public class DeviceEventHandler {

    private final DeviceEventService deviceEventService;
    private final DeviceService deviceService;

    /**
     * 处理设备事件上报消息
     *
     * @param message 设备消息
     */
    public void handle(IotDeviceMessage message) {
        try {
            // 1. 基础校验
            if (message == null || message.getDeviceId() == null) {
                log.warn("[handle][消息或设备ID为空，跳过处理]");
                return;
            }

            // 2. 从topic中提取信息
            String topic = message.getTopic();
            String[] topicParts = topic.split("/");
            if (topicParts.length < 7) {
                log.warn("[handle][Topic格式不正确，无法提取事件标识，topic: {}]", topic);
                return;
            }

            // Topic格式：/iot/{productIdentification}/{deviceIdentification}/event/upstream/report/{identifier}
            String productIdentification = topicParts.length >= 3 ? topicParts[2] : null;
            String deviceIdentification = topicParts.length >= 4 ? topicParts[3] : null;
            String eventIdentifier = topicParts.length >= 7 ? topicParts[6] : null;

            // 3. 如果deviceIdentification为空，尝试从设备服务中获取
            if (StrUtil.isBlank(deviceIdentification) && message.getDeviceId() != null) {
                com.basiclab.iot.device.domain.device.vo.Device device =
                        deviceService.findOneById(message.getDeviceId());
                if (device != null) {
                    deviceIdentification = device.getDeviceIdentification();
                    if (StrUtil.isBlank(productIdentification)) {
                        productIdentification = device.getProductIdentification();
                    }
                }
            }

            // 4. 解析事件数据
            Object params = message.getParams();
            String eventName = null;
            String eventType = null;
            String eventMessage = null;
            String status = "SUCCESS";

            if (params != null) {
                if (params instanceof Map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> paramsMap = (Map<String, Object>) params;
                    eventName = (String) paramsMap.get("eventName");
                    eventType = (String) paramsMap.get("eventType");
                    Object data = paramsMap.get("data");
                    if (data != null) {
                        eventMessage = JSONUtil.toJsonStr(data);
                    }
                    Object code = paramsMap.get("code");
                    if (code != null) {
                        status = code.toString();
                    }
                } else {
                    eventMessage = JSONUtil.toJsonStr(params);
                }
            }

            // 5. 构建设备事件实体
            DeviceEvent deviceEvent = DeviceEvent.builder()
                    .deviceIdentification(deviceIdentification)
                    .eventCode(eventIdentifier)
                    .eventName(eventName != null ? eventName : eventIdentifier)
                    .eventType(eventType != null ? eventType : "INFO")
                    .message(eventMessage)
                    .status(status)
                    .tenantId(message.getTenantId() != null ? message.getTenantId() : 0L)
                    .createTime(message.getReportTime() != null ? message.getReportTime() : LocalDateTime.now())
                    .build();

            // 6. 保存到数据库
            deviceEventService.save(deviceEvent);

            log.info("[handle][处理设备事件上报消息成功，messageId: {}, deviceId: {}, eventIdentifier: {}]",
                    message.getId(), message.getDeviceId(), eventIdentifier);

        } catch (Exception e) {
            log.error("[handle][处理设备事件上报消息失败，messageId: {}, topic: {}]",
                    message != null ? message.getId() : "unknown",
                    message != null ? message.getTopic() : "unknown", e);
            throw e;
        }
    }
}

