package com.basiclab.iot.sink.messagebus.subscriber.listener;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.sink.enums.IotDeviceTopicEnum;
import com.basiclab.iot.sink.messagebus.subscriber.event.IotMessageBusEvent;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.service.device.GatewaySubDeviceSupport;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import java.util.List;

/**
 * 处理网关拓扑上行：添加 / 删除 / 状态。
 */
@Slf4j
@Component
public class GatewayTopoUpstreamListener {

    @Resource
    private GatewaySubDeviceSupport gatewaySubDeviceSupport;

    @Async("iotMessageBusSubscriberExecutor")
    @EventListener
    public void handleTopoEvent(IotMessageBusEvent event) {
        try {
            IotDeviceTopicEnum topicEnum = event.getTopicEnum();
            if (!GatewaySubDeviceSupport.isTopoUpstream(topicEnum)) {
                return;
            }
            IotDeviceMessage message = event.getMessage();
            String gatewayIdentification = extractGatewayIdentification(message.getTopic());
            if (StrUtil.isBlank(gatewayIdentification)) {
                log.warn("[handleTopoEvent][无法解析网关标识 topic={}]", message.getTopic());
                return;
            }

            if (topicEnum == IotDeviceTopicEnum.TOPO_UPSTREAM_ADD) {
                List<Device> devices = gatewaySubDeviceSupport.processTopoAdd(
                        gatewayIdentification, message.getParams(), message.getTenantId());
                log.debug("[handleTopoEvent][拓扑添加完成 gateway={} count={}]",
                        gatewayIdentification, devices.size());
            } else if (topicEnum == IotDeviceTopicEnum.TOPO_UPSTREAM_DELETE) {
                int n = gatewaySubDeviceSupport.processTopoDelete(
                        gatewayIdentification, message.getParams());
                log.debug("[handleTopoEvent][拓扑删除完成 gateway={} count={}]", gatewayIdentification, n);
            } else if (topicEnum == IotDeviceTopicEnum.TOPO_UPSTREAM_STATUS) {
                int n = gatewaySubDeviceSupport.processTopoStatus(
                        gatewayIdentification, message.getParams());
                log.debug("[handleTopoEvent][拓扑状态更新完成 gateway={} count={}]", gatewayIdentification, n);
            }
        } catch (Exception e) {
            log.error("[handleTopoEvent][处理拓扑上行失败 topic={}]",
                    event.getMessage() != null ? event.getMessage().getTopic() : null, e);
        }
    }

    private String extractGatewayIdentification(String topic) {
        if (StrUtil.isBlank(topic)) {
            return null;
        }
        String[] parts = topic.split("/");
        // /iot/{product}/{device}/topo/...
        if (parts.length >= 4) {
            return parts[3];
        }
        return null;
    }
}
