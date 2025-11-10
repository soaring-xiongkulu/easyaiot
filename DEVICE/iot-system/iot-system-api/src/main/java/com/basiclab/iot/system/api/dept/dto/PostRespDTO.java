package com.basiclab.iot.system.api.dept.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 岗位 Response DTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "RPC 服务 - 岗位 Response DTO")
@Data
public class PostRespDTO {

    @Schema(description = "岗位编号", example = "1")
    private Long id;

    @Schema(description = "岗位名称", example = "小土豆")
    private String name;

    @Schema(description = "岗位编码", example = "Yudao")
    private String code;

    @Schema(description = "岗位排序", example = "1")
    private Integer sort;

    @Schema(description = "状态", example = "1")
    private Integer status; // 参见 CommonStatusEnum 枚举

}
