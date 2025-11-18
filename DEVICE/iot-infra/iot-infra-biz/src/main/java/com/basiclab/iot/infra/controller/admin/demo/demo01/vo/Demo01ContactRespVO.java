package com.basiclab.iot.infra.controller.admin.demo.demo01.vo;

import com.basiclab.iot.common.excels.core.annotations.DictFormat;
import com.basiclab.iot.common.excels.core.convert.DictConvert;
import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

@Schema(description = "管理后台 - 示例联系人 Response VO")
@Data
@ExcelIgnoreUnan

/**
 * Demo01ContactRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

notated
public class Demo01ContactRespVO {

    @Schema(description = "编号", example = "21555")
    @ExcelProperty("编号")
    private Long id;

    @Schema(description = "名字", example = "张三")
    @ExcelProperty("名字")
    private String name;

    @Schema(description = "性别", example = "1")
    @ExcelProperty(value = "性别", converter = DictConvert.class)
    @DictFormat("system_user_sex") // TODO 代码优化：建议设置到对应的 DictTypeConstants 枚举类中
    private Integer sex;

    @Schema(description = "出生年")
    @ExcelProperty("出生年")
    private LocalDateTime birthday;

    @Schema(description = "简介", example = "你说的对")
    @ExcelProperty("简介")
    private String description;

    @Schema(description = "头像")
    @ExcelProperty("头像")
    private String avatar;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}