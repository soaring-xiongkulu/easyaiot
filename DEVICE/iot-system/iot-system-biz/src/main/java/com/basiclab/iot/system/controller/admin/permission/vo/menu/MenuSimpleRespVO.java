package com.basiclab.iot.system.controller.admin.permission.vo.menu;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * MenuSimpleRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 菜单精简信息 Response VO")
@Data
public class MenuSimpleRespVO {

    @Schema(description = "菜单编号", example = "1024")
    private Long id;

    @Schema(description = "菜单名称", example = "BasicLab")
    private String name;

    @Schema(description = "父菜单 ID", example = "1024")
    private Long parentId;

    @Schema(description = "类型，参见 MenuTypeEnum 枚举类", example = "1")
    private Integer type;

}
