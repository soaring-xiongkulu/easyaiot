package com.basiclab.iot.sink.protocol.http.router;

import cn.hutool.core.lang.Assert;
import cn.hutool.core.util.ObjUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.extra.spring.SpringUtil;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.exception.ServiceException;
import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.util.IotDeviceAuthUtils;
import com.basiclab.iot.sink.auth.service.DeviceAuthService;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import io.vertx.core.Handler;
import io.vertx.ext.web.RoutingContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

import static com.basiclab.iot.common.exception.GlobalErrorStatus.FORBIDDEN;
import static com.basiclab.iot.common.exception.GlobalErrorStatus.INTERNAL_SERVER_ERROR;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.invalidParamException;

/**
 * IotHttpAbstractHandler
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@RequiredArgsConstructor
@Slf4j
public abstract class IotHttpAbstractHandler implements Handler<RoutingContext> {

    private final DeviceAuthService deviceAuthService = SpringUtil.getBean(DeviceAuthService.class);

    @Override
    public final void handle(RoutingContext context) {
        try {
            // 1. 前置处理
            beforeHandle(context);

            // 2. 执行逻辑
            CommonResult<Object> result = handle0(context);
            writeResponse(context, result);
        } catch (ServiceException e) {
            writeResponse(context, CommonResult.error(e.getCode(), e.getMessage()));
        } catch (Exception e) {
            log.error("[handle][path({}) 处理异常]", context.request().path(), e);
            writeResponse(context, CommonResult.error(INTERNAL_SERVER_ERROR));
        }
    }

    protected abstract CommonResult<Object> handle0(RoutingContext context);

    /**
     * 获取 HTTP 协议配置属性
     * 子类需要实现此方法以提供配置
     */
    protected abstract IotGatewayProperties.HttpProperties getHttpProperties();

    private void beforeHandle(RoutingContext context) {
        // 如果不需要认证，则不走前置处理
        String path = context.request().path();
        if (ObjUtil.equal(path, IotHttpAuthHandler.PATH)) {
            return;
        }

        // 如果关闭鉴权，则跳过 token 验证
        IotGatewayProperties.HttpProperties httpProperties = getHttpProperties();
        if (httpProperties != null && Boolean.FALSE.equals(httpProperties.getAuthEnabled())) {
            return;
        }

        // 解析参数
        String token = context.request().getHeader(HttpHeaders.AUTHORIZATION);
        if (StrUtil.isEmpty(token)) {
            throw invalidParamException("token 不能为空");
        }
        String productIdentification = context.pathParam("productIdentification");
        if (StrUtil.isEmpty(productIdentification)) {
            throw invalidParamException("productIdentification 不能为空");
        }
        String deviceIdentification = context.pathParam("deviceIdentification");
        if (StrUtil.isEmpty(deviceIdentification)) {
            throw invalidParamException("deviceIdentification 不能为空");
        }

        // 校验 token
        IotDeviceAuthUtils.DeviceInfo deviceInfo = deviceAuthService.verifyToken(token);
        Assert.notNull(deviceInfo, "设备信息不能为空");
        // 校验设备信息是否匹配
        if (ObjUtil.notEqual(productIdentification, deviceInfo.getProductIdentification())
                || ObjUtil.notEqual(deviceIdentification, deviceInfo.getDeviceIdentification())) {
            throw exception(FORBIDDEN);
        }
    }

    @SuppressWarnings("deprecation")
    public static void writeResponse(RoutingContext context, Object data) {
        context.response()
                .setStatusCode(200)
                .putHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_UTF8_VALUE)
                .end(JsonUtils.toJsonString(data));
    }

}
