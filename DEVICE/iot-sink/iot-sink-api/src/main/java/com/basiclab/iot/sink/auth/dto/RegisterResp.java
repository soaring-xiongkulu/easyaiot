package com.basiclab.iot.sink.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * RegisterResp
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Data
@Schema(description = "设备动态注册响应")
public class RegisterResp {

    /**
     * 产品标识
     */
    @Schema(description = "产品标识", example = "productKey123")
    private String productIdentification;

    /**
     * 设备标识
     */
    @Schema(description = "设备标识", example = "device123")
    private String deviceIdentification;

    /**
     * 设备密钥
     */
    @Schema(description = "设备密钥", example = "deviceSecret123")
    private String deviceSecret;

    /**
     * MQTT服务器IP地址
     */
    @Schema(description = "MQTT服务器IP地址", example = "127.0.0.1")
    private String mqttIp;

    /**
     * MQTT服务器端口
     */
    @Schema(description = "MQTT服务器端口", example = "1883")
    private Integer mqttPort;
}

