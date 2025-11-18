package com.basiclab.iot.system.api.oauth2.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * OAuth2AccessTokenRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - OAuth2 访问令牌的信息 Response DTO")
@Data
@Accessors(chain = true)
public class OAuth2AccessTokenRespDTO implements Serializable {

    @Schema(description = "访问令牌", example = "tudou")
    private String accessToken;

    @Schema(description = "刷新令牌", example = "haha")
    private String refreshToken;

    @Schema(description = "用户编号", example = "10")
    private Long userId;

    @Schema(description = "用户类型，参见 UserTypeEnum 枚举", example = "1")
    private Integer userType;

    @Schema(description = "过期时间")
    private LocalDateTime expiresTime;

}
