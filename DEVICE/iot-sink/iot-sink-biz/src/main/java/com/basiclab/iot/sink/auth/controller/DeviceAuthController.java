package com.basiclab.iot.sink.auth.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.exception.GlobalErrorStatus;
import com.basiclab.iot.device.domain.app.vo.App;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.device.domain.device.vo.Product;
import com.basiclab.iot.sink.auth.dto.RegisterReq;
import com.basiclab.iot.sink.auth.dto.RegisterResp;
import com.basiclab.iot.sink.auth.enums.SignMethod;
import com.basiclab.iot.sink.auth.service.DeviceRegisterService;
import com.basiclab.iot.sink.config.IotGatewayProperties;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.UUID;

import static com.basiclab.iot.sink.enums.ErrorCodeConstants.DEVICE_AUTH_FAIL;

/**
 * DeviceAuthController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Validated
@RestController
@RequestMapping("/iot/auth/register/device")
@Tag(name = "设备::动态注册")
@RequiredArgsConstructor
@Slf4j
public class DeviceAuthController {

    @Resource
    private DeviceRegisterService deviceRegisterService;

    @Resource
    private IotGatewayProperties gatewayProperties;

    @Operation(summary = "动态注册")
    @PostMapping
    public CommonResult<RegisterResp> register(@Validated RegisterReq req, BindingResult result) {
        // 注意：保证与 阿里云 iot 报文协议一致
        // 判断参数校验结果
        if (result.hasErrors()) {
            FieldError error = result.getFieldError();
            String message = String.format("设备动态注册: %s%s", error.getField(), error.getDefaultMessage());
            return CommonResult.error(GlobalErrorStatus.PARAM_ERROR.getCode(), message);
        }

        String signMethodStr = req.getSignMethod();
        SignMethod signMethod = SignMethod.get(signMethodStr);
        if (signMethod == null) {
            return CommonResult.error(GlobalErrorStatus.PARAM_ERROR.getCode(),
                    "设备动态注册: 签名方法错误，目前仅支持hmacmd5、hmacsha1、hmacsha256");
        }

        // 注意：由于结构体不一致，所以一些判断类的逻辑代码全写到这
        String productKey = req.getProductKey();

        // 获取产品信息
        Product product = deviceRegisterService.getProductByProductKey(productKey);
        if (product == null) {
            return CommonResult.error(GlobalErrorStatus.NOT_FOUND.getCode(), "设备动态注册: 产品不存在");
        }

        // 1. 验证AppId、AppKey、AppSecret（直接查询数据库表）
        String appId = req.getAppId();
        String appKey = req.getAppKey();
        String appSecret = req.getAppSecret();

        App app = deviceRegisterService.verifyApp(appId, appKey, appSecret);
        if (app == null) {
            return CommonResult.error(DEVICE_AUTH_FAIL.getCode(), "设备动态注册: AppId、AppKey、AppSecret验证失败");
        }

        String uniqueNo = req.getUniqueNo();
        String random = req.getRandom();

        // 2. 验证签名（使用AppSecret作为密钥）
        String content = "uniqueNo" + uniqueNo +
                "productKey" + productKey +
                "random" + random;

        String sign = req.getSign();

        // 计算、验证签名（使用AppSecret作为密钥）
        boolean signValid = deviceRegisterService.verifySign(signMethod, content, appSecret, sign);
        if (!signValid) {
            return CommonResult.error(DEVICE_AUTH_FAIL.getCode(), "设备动态注册：签名错误，请按文档签名");
        }

        // 注册设备
        Device device = deviceRegisterService.registerDevice(
                product, productKey, uniqueNo, req.getDeviceName(), req.getDeviceDesc());

        // 生成设备密钥
        // 注意：Device VO 中没有 password 字段，所以每次注册都生成新的设备密钥
        // 如果设备已存在，设备密钥应该已经在数据库中，但无法从 VO 中获取
        // 实际应用中，设备密钥应该在设备注册时由系统生成并保存到数据库
        String deviceSecret = UUID.randomUUID().toString().replace("-", "");

        // 构建注册响应
        RegisterResp registerResp = deviceRegisterService.buildRegisterResp(
                product.getProductIdentification(), device.getDeviceIdentification(), deviceSecret);

        return CommonResult.success(registerResp);
    }
}

