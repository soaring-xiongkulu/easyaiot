package com.basiclab.iot.sink.protocol.http.router;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.map.MapUtil;
import cn.hutool.core.text.StrPool;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.protocol.http.IotHttpUpstreamProtocol;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import io.vertx.ext.web.RoutingContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * IotHttpUpstreamHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@RequiredArgsConstructor
@Slf4j
public class IotHttpUpstreamHandler extends IotHttpAbstractHandler {

    public static final String PATH = "/topic/sys/:productIdentification/:deviceIdentification/*";

    private final IotHttpUpstreamProtocol protocol;

    private final IotDeviceMessageService deviceMessageService;

    public IotHttpUpstreamHandler(IotHttpUpstreamProtocol protocol) {
        this.protocol = protocol;
        this.deviceMessageService = SpringUtil.getBean(IotDeviceMessageService.class);
    }

    @Override
    protected IotGatewayProperties.HttpProperties getHttpProperties() {
        return protocol.getHttpProperties();
    }

    @Override
    protected CommonResult<Object> handle0(RoutingContext context) {
        // 1. 解析通用参数
        String productIdentification = context.pathParam("productIdentification");
        String deviceIdentification = context.pathParam("deviceIdentification");
        String method = context.pathParam("*").replaceAll(StrPool.SLASH, StrPool.DOT);

        // 2.1 解析消息
        byte[] bytes = context.body().buffer().getBytes();
        // 构建 topic
        String topic = "/iot/" + productIdentification + "/" + deviceIdentification + "/" + method;
        IotDeviceMessage message = deviceMessageService.decodeDeviceMessageByTopic(bytes, topic);
        Assert.equals(method, message.getMethod(), "method 不匹配");
        // 2.2 发送消息
        deviceMessageService.sendDeviceMessage(message,
                productIdentification, deviceIdentification, protocol.getServerId());

        // 3. 返回结果
        return CommonResult.success(MapUtil.of("messageId", message.getId()));
    }

}