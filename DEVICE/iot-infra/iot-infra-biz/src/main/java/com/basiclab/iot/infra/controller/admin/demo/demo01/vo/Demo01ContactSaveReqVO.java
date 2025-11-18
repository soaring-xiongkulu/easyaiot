package com.basiclab.iot.infra.controller.admin.demo.demo01.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.time.

/**
 * Demo01ContactSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

LocalDateTime;

@Schema(description = "管理后台 - 示例联系人新增/修改 Request VO")
@Data
public class Demo01ContactSaveReqVO {

    @Schema(description = "编号", example = "21555")
    private Long id;

    @Schema(description = "名字", example = "张三")
    @NotEmpty(message = "名字不能为空")
    private String name;

    @Schema(description = "性别", example = "1")
    @NotNull(message = "性别不能为空")
    private Integer sex;

    @Schema(description = "出生年")
    @NotNull(message = "出生年不能为空")
    private LocalDateTime birthday;

    @Schema(description = "简介", example = "你说的对")
    @NotEmpty(message = "简介不能为空")
    private String description;

    @Schema(description = "头像")
    private String avatar;

}