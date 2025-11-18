package com.basiclab.iot.device.messagebus;

import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.basiclab.iot.device.domain.device.vo.DeviceServiceInvokeResponse;
import com.basiclab.iot.device.service.device.DeviceService;
import com.basiclab.iot.device.service.device.DeviceServiceInvokeResponseService;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * ServiceInvokeResponseHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Component
@RequiredArgsConstructor
@org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)
public class ServiceInvokeResponseHandler {

    private final DeviceServiceInvokeResponseService responseService;
    private final DeviceService deviceService;

    /**
     * 处理服务调用响应消息
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
            if (topicParts.length < 6) {
                log.warn("[handle][Topic格式不正确，无法提取服务标识，topic: {}]", topic);
                return;
            }

            // Topic格式：/iot/{productIdentification}/{deviceIdentification}/service/upstream/invoke/{identifier}/response
            String productIdentification = topicParts.length >= 3 ? topicParts[2] : null;
            String deviceIdentification = topicParts.length >= 4 ? topicParts[3] : null;
            String serviceIdentifier = topicParts.length >= 7 ? topicParts[6] : null;

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

            // 4. 构建响应实体
            DeviceServiceInvokeResponse response = DeviceServiceInvokeResponse.builder()
                    .messageId(message.getId())
                    .deviceId(message.getDeviceId())
                    .deviceIdentification(deviceIdentification)
                    .productIdentification(productIdentification)
                    .serviceIdentifier(serviceIdentifier)
                    .requestId(message.getRequestId())
                    .method(message.getMethod())
                    .responseData(message.getData() != null ? JSONUtil.toJsonStr(message.getData()) : null)
                    .responseCode(message.getCode())
                    .responseMsg(message.getMsg())
                    .topic(topic)
                    .reportTime(message.getReportTime() != null ? message.getReportTime() : LocalDateTime.now())
                    .tenantId(message.getTenantId() != null ? message.getTenantId() : 0L)
                    .createTime(LocalDateTime.now())
                    .build();

            // 5. 保存到数据库
            responseService.save(response);

            log.info("[handle][处理服务调用响应消息成功，messageId: {}, deviceId: {}, serviceIdentifier: {}]",
                    message.getId(), message.getDeviceId(), serviceIdentifier);

        } catch (Exception e) {
            log.error("[handle][处理服务调用响应消息失败，messageId: {}, topic: {}]",
                    message != null ? message.getId() : "unknown",
                    message != null ? message.getTopic() : "unknown", e);
        }
    }
}

