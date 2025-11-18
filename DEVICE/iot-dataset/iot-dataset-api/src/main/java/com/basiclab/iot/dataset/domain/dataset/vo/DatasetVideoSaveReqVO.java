package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

/**
 * DatasetVideoSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频数据集新增/修改 Request VO")
@Data
public class DatasetVideoSaveReqVO {

    @Schema(description = "主键ID", example = "11001")
    private Long id;

    @Schema(description = "数据集ID", example = "18192")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "视频地址")
    @NotEmpty(message = "视频地址不能为空")
    private String videoPath;

    @Schema(description = "封面地址")
    @NotEmpty(message = "封面地址不能为空")
    private String coverPath;

    @Schema(description = "视频名称")
    @NotEmpty(message = "视频名称不能为空")
    private String name;

    @Schema(description = "描述", example = "随便")
    @NotEmpty(message = "描述不能为空")
    private String description;

}