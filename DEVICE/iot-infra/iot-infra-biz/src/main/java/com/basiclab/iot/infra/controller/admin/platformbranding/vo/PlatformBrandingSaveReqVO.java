package com.basiclab.iot.infra.controller.admin.platformbranding.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Size;

/**
 * 平台品牌配置保存请求
 */
@Schema(description = "管理后台 - 平台品牌配置保存 Request VO")
@Data
public class PlatformBrandingSaveReqVO {

    @NotBlank(message = "平台名称不能为空")
    @Size(max = 100, message = "平台名称不能超过 100 个字符")
    private String platformName;

    private Long platformLogoFileId;

    @NotBlank(message = "大屏标题不能为空")
    @Size(max = 100, message = "大屏标题不能超过 100 个字符")
    private String dashboardTitle;

    @NotBlank(message = "登录页名称不能为空")
    @Size(max = 100, message = "登录页名称不能超过 100 个字符")
    private String loginName;

    private Long loginLogoFileId;

    @Size(max = 100, message = "登录表单标题不能超过 100 个字符")
    private String loginFormTitle;

    private Long loginBgLightFileId;

    private Long loginBgDarkFileId;
}
