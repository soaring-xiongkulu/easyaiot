package com.basiclab.iot.sink.biz.config;

import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.AutoConfiguration;

/**
 * IoT 下行消息发送 API 自动配置
 * <p>
 * 实现类 IotDownstreamMessageApiImpl 在 sink-api 模块中，使用 @Service 注解自动注册
 * <p>
 * 此配置类用于确保必要的依赖（IotDeviceMessageProducer 和 DeviceServerIdService）存在
 * <p>
 * 其他模块可以通过依赖 sink-api 来使用此 API，无需关心具体实现
 * <p>
 * 注意：如果 DeviceServerIdService 的实现类不存在，sendDownstreamMessageByDeviceId 方法
 * 会降级为发送到通用 Topic
 *
 * @author 翱翔的雄库鲁
 */
@AutoConfiguration
@Slf4j
public class IotDownstreamMessageApiAutoConfiguration {

    // 实现类 IotDownstreamMessageApiImpl 在 sink-api 模块中，使用 @Service 注解自动注册
    // 不需要手动创建 Bean，Spring 会自动扫描并注册
    // 只需要确保 IotDeviceMessageProducer 和 DeviceServerIdService 存在即可

}

