package com.basiclab.iot.infra.controller.admin.demo.demo02.vo;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * Demo02CategoryRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 示例分类 Response VO")
@Data
@ExcelIgnoreUnannotated
public class Demo02CategoryRespVO {

    @Schema(description = "编号", example = "10304")
    @ExcelProperty("编号")
    private Long id;

    @Schema(description = "名字", example = "BasicLab")
    @ExcelProperty("名字")
    private String name;

    @Schema(description = "父级编号", example = "6080")
    @ExcelProperty("父级编号")
    private Long parentId;

    @Schema(description = "创建时间")
    @ExcelProperty("创建时间")
    private LocalDateTime createTime;

}