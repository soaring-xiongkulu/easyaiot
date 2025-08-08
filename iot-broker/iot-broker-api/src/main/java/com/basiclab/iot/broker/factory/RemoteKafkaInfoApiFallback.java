package com.basiclab.iot.broker.factory;

import com.basiclab.iot.broker.RemoteKafkaInfoApi;
import com.basiclab.iot.broker.domain.vo.KafkaMessageRequestVO;
import com.basiclab.iot.common.domain.R;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-06-07
 */
@Component
@Slf4j
public class RemoteKafkaInfoApiFallback implements FallbackFactory<RemoteKafkaInfoApi> {
    @Override
    public RemoteKafkaInfoApi create(Throwable cause) {
        log.error("Broker推送设备消息服务调用失败:{}", cause.getMessage());
        return new RemoteKafkaInfoApi() {
            @Override
            public R<?> sendMessage(KafkaMessageRequestVO kafkaMessageRequestVO) {
                return R.fail("remoteMqttBrokerOpenApi.sendMessage() Service call failure e:{}", cause.getMessage());
            }
        };
    }
}
