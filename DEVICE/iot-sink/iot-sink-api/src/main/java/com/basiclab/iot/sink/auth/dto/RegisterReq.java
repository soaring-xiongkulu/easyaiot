package com.basiclab.iot.sink.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;

/**
 * RegisterReq
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Data
@Schema(description = "设备动态注册请求")
public class RegisterReq {

    /**
     * 产品标识
     */
    @NotBlank(message = "产品标识不能为空")
    @Schema(description = "产品标识", required = true, example = "productKey123")
    private String productKey;

    /**
     * 设备唯一标识
     */
    @NotBlank(message = "设备唯一标识不能为空")
    @Schema(description = "设备唯一标识", required = true, example = "device123")
    private String uniqueNo;

    /**
     * 随机数
     */
    @NotBlank(message = "随机数不能为空")
    @Schema(description = "随机数", required = true, example = "random123")
    private String random;

    /**
     * 签名方法
     */
    @NotBlank(message = "签名方法不能为空")
    @Schema(description = "签名方法，支持：hmacmd5、hmacsha1、hmacsha256", required = true, example = "hmacsha256")
    private String signMethod;

    /**
     * 签名
     */
    @NotBlank(message = "签名不能为空")
    @Schema(description = "签名", required = true)
    private String sign;

    /**
     * 设备名称（可选）
     */
    @Schema(description = "设备名称", example = "我的设备")
    private String deviceName;

    /**
     * 设备描述（可选）
     */
    @Schema(description = "设备描述", example = "设备描述信息")
    private String deviceDesc;

    /**
     * 租户ID（可选）
     */
    @Schema(description = "租户ID", example = "1")
    private String tenantId;

    /**
     * 应用ID（AppID）：应用的唯一标识
     */
    @NotBlank(message = "应用ID不能为空")
    @Schema(description = "应用ID（AppID）", required = true, example = "abc12345")
    private String appId;

    /**
     * 应用密钥（AppKey）：公匙，相当于账号
     */
    @NotBlank(message = "应用密钥不能为空")
    @Schema(description = "应用密钥（AppKey）", required = true, example = "def67890")
    private String appKey;

    /**
     * 应用密钥（AppSecret）：私匙，相当于密码
     */
    @NotBlank(message = "应用密钥不能为空")
    @Schema(description = "应用密钥（AppSecret）", required = true)
    private String appSecret;
}

