package com.basiclab.iot.system.api.oauth2.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * OAuth2AccessTokenCheckRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - OAuth2 访问令牌的校验 Response DTO")
@Data
public class OAuth2AccessTokenCheckRespDTO implements Serializable {

    @Schema(description = "用户编号", example = "10")
    private Long userId;

    @Schema(description = "用户类型，参见 UserTypeEnum 枚举", example = "1")
    private Integer userType;

    @Schema(description = "用户信息", example = "{\"nickname\": \"BasicLab\"}")
    private Map<String, String> userInfo;

    @Schema(description = "租户编号", example = "1024")
    private Long tenantId;

    @Schema(description = "授权范围的数组", example = "user_info")
    private List<String> scopes;

}
