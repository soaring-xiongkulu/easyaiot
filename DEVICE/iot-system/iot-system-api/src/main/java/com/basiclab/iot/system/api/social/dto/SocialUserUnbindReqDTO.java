package com.basiclab.iot.system.api.social.dto;

import com.basiclab.iot.common.enums.UserTypeEnum;
import com.basiclab.iot.common.validation.InEnum;
import com.basiclab.iot.system.enums.social.SocialTypeEnum;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

/**
 * SocialUserUnbindReqDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 取消绑定社交用户 Request DTO")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class SocialUserUnbindReqDTO {

    @Schema(description = "用户编号", example = "1024")
    @NotNull(message = "用户编号不能为空")
    private Long userId;
    @Schema(description = "用户类型", example = "1")
    @InEnum(UserTypeEnum.class)
    @NotNull(message = "用户类型不能为空")
    private Integer userType;

    @Schema(description = "社交平台的类型", example = "1")
    @InEnum(SocialTypeEnum.class)
    @NotNull(message = "社交平台的类型不能为空")
    private Integer socialType;
    @Schema(description = "社交平台的 openid", example = "zsw")
    @NotEmpty(message = "社交平台的 openid 不能为空")
    private String openid;

}
