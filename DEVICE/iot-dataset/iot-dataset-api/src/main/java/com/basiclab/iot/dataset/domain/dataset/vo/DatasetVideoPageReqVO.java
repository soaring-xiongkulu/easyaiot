package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;

/**
 * DatasetVideoPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 视频数据集分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetVideoPageReqVO extends PageParam {

    @Schema(description = "数据集ID", example = "18192")
    private Long datasetId;

    @Schema(description = "视频地址")
    private String videoPath;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "视频名称")
    private String name;

    @Schema(description = "描述", example = "随便")
    private String description;

}