package com.basiclab.iot.dataset.domain.warehouse.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

/**
 * WarehouseRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据仓 Response VO")
@Data
@ExcelIgnoreUnannotated
public class WarehouseRespVO {

    @Schema(description = "主键ID", example = "21541")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "仓库名称", example = "李四")
    @ExcelProperty("仓库名称")
    private String name;

    @Schema(description = "封面地址")
    @ExcelProperty("封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    @ExcelProperty("描述")
    private String description;

}