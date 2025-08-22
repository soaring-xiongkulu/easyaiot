package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

import javax.validation.constraints.*;

@Schema(description = "管理后台 - 数据集新增/修改 Request VO")
@Data
public class DatasetSaveReqVO {

    @Schema(description = "主键ID", example = "22596")
    private Long id;

    @Schema(description = "数据集编码")
    private String datasetCode;

    @Schema(description = "数据集名称", example = "张三")
    @NotEmpty(message = "数据集名称不能为空")
    private String name;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    private String description;

    @Schema(description = "数据集类型，0-图片；1-文本", example = "0")
    @NotNull(message = "数据集类型，1-图片；2-文本不能为空")
    private Integer datasetType;

    @Schema(description = "数据集状态：0-待审核；1-审核通过；2-驳回")
    private Integer audit;

    @Schema(description = "审核驳回理由", example = "不好")
    private String reason;

    @Schema(description = "数据集压缩包下载地址")
    private String zipUrl;
}