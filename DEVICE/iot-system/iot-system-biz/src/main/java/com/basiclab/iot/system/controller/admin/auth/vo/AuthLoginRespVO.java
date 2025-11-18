package com.basiclab.iot.system.controller.admin.auth.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * AuthLoginRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 登录 Response VO")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AuthLoginRespVO {

    @Schema(description = "用户编号", example = "1024")
    private Long userId;

    @Schema(description = "访问令牌", example = "happy")
    private String accessToken;

    @Schema(description = "刷新令牌", example = "nice")
    private String refreshToken;

    @Schema(description = "过期时间")
    private LocalDateTime expiresTime;

}
