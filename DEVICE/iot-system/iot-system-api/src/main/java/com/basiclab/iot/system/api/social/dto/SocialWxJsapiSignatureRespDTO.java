package com.basiclab.iot.system.api.social.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * SocialWxJsapiSignatureRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 微信公众号 JSAPI 签名 Response DTO")
@Data
public class SocialWxJsapiSignatureRespDTO {

    @Schema(description = "微信公众号的 appId", example = "wx123456")
    private String appId;

    @Schema(description = "匿名串", example = "zsw")
    private String nonceStr;

    @Schema(description = "时间戳", example = "123456789")
    private Long timestamp;

    @Schema(description = "URL", example = "https://www.iocoder.cn")
    private String url;

    @Schema(description = "签名", example = "zsw")
    private String signature;

}
