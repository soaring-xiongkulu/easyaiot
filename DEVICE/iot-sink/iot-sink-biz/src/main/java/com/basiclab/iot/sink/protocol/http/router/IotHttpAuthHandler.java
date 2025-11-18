package com.basiclab.iot.sink.protocol.http.router;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.map.MapUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.sink.auth.service.DeviceAuthService;
import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;
import com.basiclab.iot.sink.util.IotDeviceAuthUtils;
import com.basiclab.iot.sink.protocol.http.IotHttpUpstreamProtocol;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.messagebus.publisher.message.IotDeviceMessageService;
import io.vertx.core.json.JsonObject;
import io.vertx.ext.web.RoutingContext;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.invalidParamException;
import static com.basiclab.iot.common.domain.CommonResult.success;
import static com.basiclab.iot.sink.enums.ErrorCodeConstants.DEVICE_AUTH_FAIL;

/**
 * IotHttpAuthHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public class IotHttpAuthHandler extends IotHttpAbstractHandler {

    public static final String PATH = "/auth";

    private final IotHttpUpstreamProtocol protocol;

    private final DeviceAuthService deviceAuthService;

    private final IotDeviceMessageService deviceMessageService;

    public IotHttpAuthHandler(IotHttpUpstreamProtocol protocol) {
        this.protocol = protocol;
        this.deviceAuthService = SpringUtil.getBean(DeviceAuthService.class);
        this.deviceMessageService = SpringUtil.getBean(IotDeviceMessageService.class);
    }

    @Override
    protected IotGatewayProperties.HttpProperties getHttpProperties() {
        return protocol.getHttpProperties();
    }

    @Override
    public CommonResult<Object> handle0(RoutingContext context) {
        // 1. 解析参数
        JsonObject body = context.body().asJsonObject();
        String clientId = body.getString("clientId");
        if (StrUtil.isEmpty(clientId)) {
            throw invalidParamException("clientId 不能为空");
        }
        String username = body.getString("username");
        if (StrUtil.isEmpty(username)) {
            throw invalidParamException("username 不能为空");
        }
        String password = body.getString("password");
        if (StrUtil.isEmpty(password)) {
            throw invalidParamException("password 不能为空");
        }

        // 2. 如果开启鉴权，则执行认证
        IotDeviceAuthUtils.DeviceInfo deviceInfo;
        if (Boolean.TRUE.equals(protocol.getHttpProperties().getAuthEnabled())) {
            // 2.1 执行认证
            boolean authResult = deviceAuthService.authDevice(new IotDeviceAuthReqDTO()
                    .setClientId(clientId).setUsername(username).setPassword(password));
            if (!authResult) {
                throw exception(DEVICE_AUTH_FAIL);
            }
            // 2.2 解析设备信息
            deviceInfo = deviceAuthService.parseUsername(username);
            Assert.notNull(deviceInfo, "设备信息不能为空");
        } else {
            // 如果不开启鉴权，直接解析 username 获取设备信息
            deviceInfo = deviceAuthService.parseUsername(username);
            Assert.notNull(deviceInfo, "设备信息不能为空");
        }

        // 3. 生成 Token
        String token = deviceAuthService.createToken(deviceInfo.getProductIdentification(), deviceInfo.getDeviceIdentification());
        Assert.notBlank(token, "生成 token 不能为空位");

        // 4. 执行上线
        IotDeviceMessage message = IotDeviceMessage.buildStateUpdateOnline();
        deviceMessageService.sendDeviceMessage(message,
                deviceInfo.getProductIdentification(), deviceInfo.getDeviceIdentification(), protocol.getServerId());

        // 构建响应数据
        return success(MapUtil.of("token", token));
    }

}
