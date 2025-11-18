package com.basiclab.iot.system.controller.admin.oauth2.vo.open;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * OAuth2OpenAccessTokenRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 【开放接口】访问令牌 Response VO")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class OAuth2OpenAccessTokenRespVO {

    @Schema(description = "访问令牌", example = "tudou")
    @JsonProperty("access_token")
    private String accessToken;

    @Schema(description = "刷新令牌", example = "nice")
    @JsonProperty("refresh_token")
    private String refreshToken;

    @Schema(description = "令牌类型", example = "bearer")
    @JsonProperty("token_type")
    private String tokenType;

    @Schema(description = "过期时间,单位：秒", example = "42430")
    @JsonProperty("expires_in")
    private Long expiresIn;

    @Schema(description = "授权范围,如果多个授权范围，使用空格分隔", example = "user_info")
    private String scope;

}
