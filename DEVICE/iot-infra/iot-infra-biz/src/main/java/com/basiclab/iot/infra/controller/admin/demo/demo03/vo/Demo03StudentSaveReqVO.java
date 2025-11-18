package com.basiclab.iot.infra.controller.admin.demo.demo03.vo;

import com.basiclab.iot.infra.dal.dataobject.demo.demo03.Demo03CourseDO;
import com.basiclab.iot.infra.dal.dataobject.demo.demo03.Demo03GradeDO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;
import java.time.

/**
 * Demo03StudentSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

LocalDateTime;
import java.util.List;

@Schema(description = "管理后台 - 学生新增/修改 Request VO")
@Data
public class Demo03StudentSaveReqVO {

    @Schema(description = "编号", example = "8525")
    private Long id;

    @Schema(description = "名字", example = "BasicLab")
    @NotEmpty(message = "名字不能为空")
    private String name;

    @Schema(description = "性别")
    @NotNull(message = "性别不能为空")
    private Integer sex;

    @Schema(description = "出生日期")
    @NotNull(message = "出生日期不能为空")
    private LocalDateTime birthday;

    @Schema(description = "简介", example = "随便")
    @NotEmpty(message = "简介不能为空")
    private String description;

    private List<Demo03CourseDO> demo03Courses;

    private Demo03GradeDO demo03Grade;

}