package com.basiclab.iot.infra.controller.admin.demo.demo03.vo;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Demo03StudentRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 学生 Response VO")
@Data
@ExcelIgnoreUnannotated
public class Demo03StudentRespVO {

    @Schema(description = "编号", example = "8525")
    @ExcelProperty("编号")
    private Long id;

    @Schema(description = "名字", example = "BasicLab")
    @ExcelProperty("名字")
    private String name;

    @Schema(description = "性别")
    @ExcelProperty(value = "性别", converter = DictConvert.class)
    @DictFormat("system_user_sex") // TODO 代码优化：建议设置到对应的 DictTypeConstants 枚举类中
    private Integer sex;

    @Schema(description = "出生日期")
    @ExcelProperty("出生日期")
    private LocalDateTime birthday;

    @Schema(description = "简介", example = "随便")
    @ExcelProperty("简介")
    private String description;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}