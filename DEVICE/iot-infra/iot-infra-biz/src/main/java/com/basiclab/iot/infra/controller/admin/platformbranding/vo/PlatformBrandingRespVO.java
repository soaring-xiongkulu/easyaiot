package com.basiclab.iot.infra.controller.admin.platformbranding.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 平台品牌配置响应
 */
@Schema(description = "管理后台 - 平台品牌配置 Response VO")
@Data
public class PlatformBrandingRespVO {

    private String platformName;

    private Long platformLogoFileId;

    private String platformLogo;

    private String dashboardTitle;

    private String loginName;

    private Long loginLogoFileId;

    private String loginLogo;

    private String loginFormTitle;

    private Long loginBgLightFileId;

    private String loginBgLight;

    private Long loginBgDarkFileId;

    private String loginBgDark;
}
