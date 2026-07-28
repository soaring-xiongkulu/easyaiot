package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Schema(description = "数据集同步前置检查")
@Data
@Builder
public class DatasetSyncCheckRespVO {

    @Schema(description = "用途是否已划分")
    private Boolean usageAllocated;

    @Schema(description = "标注是否全部完成")
    private Boolean annotationCompleted;

    @Schema(description = "是否满足同步条件")
    private Boolean syncReady;

    @Schema(description = "是否正在同步")
    private Boolean syncing;

    @Schema(description = "是否已同步到 MinIO")
    private Boolean syncedToMinio;

    @Schema(description = "最近一次同步错误")
    private String syncError;

    @Schema(description = "同步状态：IDLE、QUEUED、RUNNING、SUCCEEDED、FAILED")
    private String syncStatus;

    @Schema(description = "同步阶段：WAITING、PREPARING、EXPORTING、PACKAGING、UPLOADING、FINALIZING、COMPLETED、FAILED")
    private String syncStage;

    @Schema(description = "同步进度，0-100")
    private Integer syncProgress;

    @Schema(description = "已处理图片数")
    private Integer processedImages;

    @Schema(description = "任务提交时间")
    private Instant syncSubmittedAt;

    @Schema(description = "任务开始时间")
    private Instant syncStartedAt;

    @Schema(description = "任务结束时间")
    private Instant syncFinishedAt;

    @Schema(description = "图片总数")
    private Integer totalImages;

    @Schema(description = "未划分用途数量")
    private Integer unallocatedCount;

    @Schema(description = "未完成标注数量")
    private Integer unannotatedCount;
}
