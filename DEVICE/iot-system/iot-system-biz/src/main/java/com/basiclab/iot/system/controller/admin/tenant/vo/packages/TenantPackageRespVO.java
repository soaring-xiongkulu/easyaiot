package com.basiclab.iot.system.controller.admin.tenant.vo.packages;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.Set;

@Schema(description = "管理后台 - 租户套餐 Response VO")
@

/**
 * TenantPackageRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

Data
public class TenantPackageRespVO {

    @Schema(description = "套餐编号", example = "1024")
    private Long id;

    @Schema(description = "套餐名", example = "VIP")
    private String name;

    @Schema(description = "状态，参见 CommonStatusEnum 枚举", example = "1")
    private Integer status;

    @Schema(description = "备注", example = "好")
    private String remark;

    @Schema(description = "关联的菜单编号")
    private Set<Long> menuIds;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
