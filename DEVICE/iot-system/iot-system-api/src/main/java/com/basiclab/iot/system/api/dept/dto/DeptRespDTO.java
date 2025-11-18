package com.basiclab.iot.system.api.dept.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * DeptRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 部门 Response DTO")
@Data
public class DeptRespDTO {

    @Schema(description = "部门编号", example = "1")
    private Long id;

    @Schema(description = "部门名称", example = "研发部")
    private String name;

    @Schema(description = "父部门编号", example = "1")
    private Long parentId;

    @Schema(description = "负责人的用户编号", example = "1")
    private Long leaderUserId;

    @Schema(description = "部门状态", example = "1")
    private Integer status; // 参见 CommonStatusEnum 枚举

}
