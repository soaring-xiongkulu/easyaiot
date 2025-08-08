package com.basiclab.iot.system.controller.admin.socail.vo.client;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.common.enums.CommonStatusEnum;
import com.basiclab.iot.common.enums.UserTypeEnum;
import com.basiclab.iot.common.validation.InEnum;
import com.basiclab.iot.system.enums.social.SocialTypeEnum;
import com.fasterxml.jackson.annotation.JsonIgnore;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.AssertTrue;
import javax.validation.constraints.NotNull;
import java.util.Objects;

@Schema(description = "管理后台 - 社交客户端创建/修改 Request VO")
@Data
public class SocialClientSaveReqVO {

    @Schema(description = "编号", example = "27162")
    private Long id;

    @Schema(description = "应用名", example = "Yudao商城")
    @NotNull(message = "应用名不能为空")
    private String name;

    @Schema(description = "社交平台的类型", example = "31")
    @NotNull(message = "社交平台的类型不能为空")
    @InEnum(SocialTypeEnum.class)
    private Integer socialType;

    @Schema(description = "用户类型", example = "2")
    @NotNull(message = "用户类型不能为空")
    @InEnum(UserTypeEnum.class)
    private Integer userType;

    @Schema(description = "客户端编号", example = "wwd411c69a39ad2e54")
    @NotNull(message = "客户端编号不能为空")
    private String clientId;

    @Schema(description = "客户端密钥", example = "peter")
    @NotNull(message = "客户端密钥不能为空")
    private String clientSecret;

    @Schema(description = "授权方的网页应用编号", example = "2000045")
    private String agentId;

    @Schema(description = "状态", example = "1")
    @NotNull(message = "状态不能为空")
    @InEnum(CommonStatusEnum.class)
    private Integer status;

    @AssertTrue(message = "agentId 不能为空")
    @JsonIgnore
    public boolean isAgentIdValid() {
        // 如果是企业微信，必须填写 agentId 属性
        return !Objects.equals(socialType, SocialTypeEnum.WECHAT_ENTERPRISE.getType())
                || !StrUtil.isEmpty(agentId);
    }

}
