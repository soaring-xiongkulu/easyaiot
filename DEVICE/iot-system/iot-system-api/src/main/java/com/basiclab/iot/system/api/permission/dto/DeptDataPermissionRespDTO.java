package com.basiclab.iot.system.api.permission.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.HashSet;
import java.util.Set;

/**
 * DeptDataPermissionRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 部门的数据权限 Response DTO")
@Data
public class DeptDataPermissionRespDTO {

    @Schema(description = "是否可查看全部数据", example = "true")
    private Boolean all;

    @Schema(description = "是否可查看自己的数据", example = "true")
    private Boolean self;

    @Schema(description = "可查看的部门编号数组", example = "[1, 3]")
    private Set<Long> deptIds;

    public DeptDataPermissionRespDTO() {
        this.all = false;
        this.self = false;
        this.deptIds = new HashSet<>();
    }

}
