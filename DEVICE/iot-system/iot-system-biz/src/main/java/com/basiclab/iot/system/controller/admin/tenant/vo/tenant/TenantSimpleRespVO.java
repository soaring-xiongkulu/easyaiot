package com.basiclab.iot.system.controller.admin.tenant.vo.tenant;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Schema(description = "管理后台 - 租户精简 Response VO")
@Data
public class TenantSimpleRespVO {

    @Schema(de

/**
 * TenantSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

scription = "租户编号", example = "1024")
    private Long id;

    @Schema(description = "租户名", example = "BasicLab")
    private String name;

}
