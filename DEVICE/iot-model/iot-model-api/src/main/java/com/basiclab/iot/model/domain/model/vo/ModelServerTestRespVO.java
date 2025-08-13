package com.basiclab.iot.model.domain.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import java.time.LocalDateTime;
import com.alibaba.excel.annotation.*;

@Schema(description = "管理后台 - 模型测试服务 Response VO")
@Data
@ExcelIgnoreUnannotated
public class ModelServerTestRespVO {

    @Schema(description = "主键ID", example = "10970")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "模型服务ID", example = "23393")
    @ExcelProperty("模型服务ID")
    private Long modelServeId;

    @Schema(description = "模型ID", example = "23378")
    @ExcelProperty("模型ID")
    private Long modelId;

    @Schema(description = "测试模型服务名称", example = "王五")
    @ExcelProperty("测试模型服务名称")
    private String name;

    @Schema(description = "测试模型服务类型[0:图片测试,1:视频测试]", example = "2")
    @ExcelProperty("测试模型服务类型[0:图片测试,1:视频测试]")
    private Short type;

    @Schema(description = "计划标注数量")
    @ExcelProperty("计划标注数量")
    private Integer plannedQuantity;

    @Schema(description = "已经标注数量")
    @ExcelProperty("已经标注数量")
    private Integer markedQuantity;

    @Schema(description = "无目标数量", example = "3115")
    @ExcelProperty("无目标数量")
    private Integer notTargetCount;

    @Schema(description = "完成时间")
    @ExcelProperty("完成时间")
    private LocalDateTime finishTime;

    @Schema(description = "服务状态[0:进行中,1:成功,2:失败]")
    @ExcelProperty("服务状态[0:进行中,1:成功,2:失败]")
    private Short state;

    @Schema(description = "描述", example = "随便")
    @ExcelProperty("描述")
    private String description;

}