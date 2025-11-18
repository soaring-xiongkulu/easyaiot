package com.basiclab.iot.dataset.domain.dataset.vo;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import com.basiclab.iot.common.domain.PageParam;

/**
 * DatasetPageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据集分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetPageReqVO extends PageParam {

    @Schema(description = "数据集编码")
    private String datasetCode;

    @Schema(description = "数据集名称", example = "张三")
    private String name;

    @Schema(description = "封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    private String description;

    @Schema(description = "数据集类型，0-图片；1-文本", example = "0")
    private Integer datasetType;

    @Schema(description = "数据集状态：0-待审核；1-审核通过；2-驳回")
    private Integer audit;

    @Schema(description = "审核驳回理由", example = "不好")
    private String reason;

    @Schema(description = "图片总数")
    private Integer totalImages;

    @Schema(description = "已标注图片数")
    private Integer annotatedImages;

}