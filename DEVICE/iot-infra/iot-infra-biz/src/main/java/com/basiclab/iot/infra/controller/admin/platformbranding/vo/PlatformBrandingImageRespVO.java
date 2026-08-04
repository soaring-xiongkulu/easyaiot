package com.basiclab.iot.infra.controller.admin.platformbranding.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;

/**
 * 平台品牌图片上传响应
 */
@Schema(description = "管理后台 - 平台品牌图片上传 Response VO")
@Data
@AllArgsConstructor
public class PlatformBrandingImageRespVO {

    private Long fileId;

    private String url;
}
