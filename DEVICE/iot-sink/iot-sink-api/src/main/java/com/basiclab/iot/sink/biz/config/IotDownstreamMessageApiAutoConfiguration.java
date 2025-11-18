package com.basiclab.iot.sink.biz.config;

import com.basiclab.iot.sink.mq.producer.IotDeviceMessageProducer;
import com.basiclab.iot.sink.service.DeviceServerIdService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.AutoConfiguration;

/**
 * IotDownstreamMessageApiAutoConfiguration
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@AutoConfiguration
@Slf4j
public class IotDownstreamMessageApiAutoConfiguration {

    // 实现类 IotDownstreamMessageApiImpl 在 sink-api 模块中，使用 @Service 注解自动注册
    // 不需要手动创建 Bean，Spring 会自动扫描并注册
    // 只需要确保 IotDeviceMessageProducer 和 DeviceServerIdService 存在即可

}

