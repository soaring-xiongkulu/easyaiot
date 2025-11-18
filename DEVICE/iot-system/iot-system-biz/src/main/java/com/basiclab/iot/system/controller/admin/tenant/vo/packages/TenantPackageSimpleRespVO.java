package com.basiclab.iot.system.controller.admin.tenant.vo.packages;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

/**
 * TenantPackageSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 租户套餐精简 Response VO")
@Data
public class TenantPackageSimpleRespVO {

    @Schema(description = "套餐编号", example = "1024")
    @NotNull(message = "套餐编号不能为空")
    private Long id;

    @Schema(description = "套餐名", example = "VIP")
    @NotNull(message = "套餐名不能为空")
    private String name;

}
