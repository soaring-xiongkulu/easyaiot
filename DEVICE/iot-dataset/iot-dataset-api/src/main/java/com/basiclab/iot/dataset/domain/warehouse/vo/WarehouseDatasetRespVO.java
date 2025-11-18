package com.basiclab.iot.dataset.domain.warehouse.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

/**
 * WarehouseDatasetRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据仓数据集关联 Response VO")
@Data
@ExcelIgnoreUnannotated
public class WarehouseDatasetRespVO {

    @Schema(description = "主键ID", example = "2401")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "数据集ID", example = "24462")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "数据仓ID", example = "28615")
    @ExcelProperty("数据仓ID")
    private Long warehouseId;

    @Schema(description = "计划同步数量", example = "15407")
    @ExcelProperty("计划同步数量")
    private Integer planSyncCount;

    @Schema(description = "已同步数量", example = "13675")
    @ExcelProperty("已同步数量")
    private Integer syncCount;

    @Schema(description = "同步状态[0:未同步,1:同步中,2:同步完成]", example = "2")
    @ExcelProperty("同步状态[0:未同步,1:同步中,2:同步完成]")
    private Integer syncStatus;

    @Schema(description = "同步失败数量", example = "20923")
    @ExcelProperty("同步失败数量")
    private Integer failCount;

}