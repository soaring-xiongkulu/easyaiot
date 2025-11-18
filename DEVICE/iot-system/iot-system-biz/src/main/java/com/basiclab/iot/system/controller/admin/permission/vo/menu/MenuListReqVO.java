package com.basiclab.iot.system.controller.admin.permission.vo.menu;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * MenuListReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 菜单列表 Request VO")
@Data
public class MenuListReqVO {

    @Schema(description = "菜单名称，模糊匹配", example = "BasicLab")
    private String name;

    @Schema(description = "展示状态，参见 CommonStatusEnum 枚举类", example = "1")
    private Integer status;

}
