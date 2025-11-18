package com.basiclab.iot.sink.auth.service;

import cn.hutool.core.lang.Assert;
import cn.hutool.json.JSONObject;
import cn.hutool.jwt.JWT;
import cn.hutool.jwt.JWTUtil;
import com.basiclab.iot.common.utils.date.LocalDateTimeUtils;
import com.basiclab.iot.sink.biz.dto.IotDeviceAuthReqDTO;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import com.basiclab.iot.sink.dal.dataobject.DeviceDO;
import com.basiclab.iot.sink.service.device.DeviceService;
import com.basiclab.iot.sink.util.IotDeviceAuthUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.sink.enums.ErrorCodeConstants.DEVICE_TOKEN_EXPIRED;

/**
 * DeviceAuthServiceImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Service
@Slf4j
public class DeviceAuthServiceImpl implements DeviceAuthService {

    @Resource
    private DeviceService deviceService;

    @Resource
    private IotGatewayProperties gatewayProperties;

    @Override
    public boolean authDevice(IotDeviceAuthReqDTO authReqDTO) {
        Assert.notNull(authReqDTO, "认证请求不能为空");
        Assert.notBlank(authReqDTO.getClientId(), "客户端 ID 不能为空");
        Assert.notBlank(authReqDTO.getUsername(), "用户名不能为空");
        Assert.notBlank(authReqDTO.getPassword(), "密码不能为空");

        // 解析用户名获取产品标识和设备名称
        IotDeviceAuthUtils.DeviceInfo deviceInfo = parseUsername(authReqDTO.getUsername());
        if (deviceInfo == null) {
            log.warn("[authDevice][解析设备信息失败，username: {}]", authReqDTO.getUsername());
            return false;
        }

        // 从数据库查询设备信息进行认证
        // 设备状态：ENABLE 表示启用
        // 协议类型：默认使用 MQTT，也可以从配置中获取
        DeviceDO device = deviceService.getDeviceForAuth(
                authReqDTO.getClientId(),
                authReqDTO.getUsername(),
                authReqDTO.getPassword(),
                "ENABLE", // 设备状态：启用
                "MQTT"   // 协议类型：MQTT
        );

        if (device == null) {
            log.warn("[authDevice][设备认证失败，clientId: {}, username: {}]", 
                    authReqDTO.getClientId(), authReqDTO.getUsername());
            return false;
        }

        log.info("[authDevice][设备认证成功，设备 ID: {}, 设备唯一标识: {}]", 
                device.getId(), device.getDeviceIdentification());
        return true;
    }

    @Override
    public String createToken(String productIdentification, String deviceIdentification) {
        Assert.notBlank(productIdentification, "productIdentification 不能为空");
        Assert.notBlank(deviceIdentification, "deviceIdentification 不能为空");
        // 构建 JWT payload
        Map<String, Object> payload = new HashMap<>();
        payload.put("productIdentification", productIdentification);
        payload.put("deviceIdentification", deviceIdentification);
        LocalDateTime expireTime = LocalDateTimeUtils.addTime(gatewayProperties.getToken().getExpiration());
        payload.put("exp", LocalDateTimeUtils.toEpochSecond(expireTime)); // 过期时间（exp 是 JWT 规范推荐）

        // 生成 JWT Token
        return JWTUtil.createToken(payload, gatewayProperties.getToken().getSecret().getBytes());
    }

    @Override
    public IotDeviceAuthUtils.DeviceInfo verifyToken(String token) {
        Assert.notBlank(token, "token 不能为空");
        // 校验 JWT Token
        boolean verify = JWTUtil.verify(token, gatewayProperties.getToken().getSecret().getBytes());
        if (!verify) {
            throw exception(DEVICE_TOKEN_EXPIRED);
        }

        // 解析 Token
        JWT jwt = JWTUtil.parseToken(token);
        JSONObject payload = jwt.getPayloads();
        // 检查过期时间
        Long exp = payload.getLong("exp");
        if (exp == null || exp < System.currentTimeMillis() / 1000) {
            throw exception(DEVICE_TOKEN_EXPIRED);
        }
        // 向后兼容：优先使用新字段，如果没有则使用旧字段
        String productIdentification = payload.getStr("productIdentification");
        String deviceIdentification = payload.getStr("deviceIdentification");
        Assert.notBlank(productIdentification, "productIdentification 不能为空");
        Assert.notBlank(deviceIdentification, "deviceIdentification 不能为空");
        return new IotDeviceAuthUtils.DeviceInfo().setProductIdentification(productIdentification).setDeviceIdentification(deviceIdentification);
    }

    @Override
    public IotDeviceAuthUtils.DeviceInfo parseUsername(String username) {
        return IotDeviceAuthUtils.parseUsername(username);
    }
}

