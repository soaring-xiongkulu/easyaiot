package com.basiclab.iot.dataset.domain.dataset.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotNull;

/**
 * DatasetImageSaveReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 图片数据集新增/修改 Request VO")
@Data
public class DatasetImageSaveReqVO {

    @Schema(description = "主键ID", example = "17489")
    private Long id;

    @Schema(description = "数据集ID", example = "1569")
    @NotNull(message = "数据集ID不能为空")
    private Long datasetId;

    @Schema(description = "图片名称", example = "张三")
    private String name;

    @Schema(description = "图片地址")
    private String path;

    @Schema(description = "标注信息，JSON格式")
    private String annotations;

    @Schema(description = "图片宽度")
    private Integer width;

    @Schema(description = "图片高度")
    private Integer heigh;

    @Schema(description = "图片大小")
    private Long size;

    @Schema(description = "视频ID（来源为视频切片）", example = "21383")
    private Long datasetVideoId;

    @Schema(description = "是否标注完成", example = "true/false")
    private Integer completed;

    @Schema(description = "最后修改时间", example = "2025-06-24T13:10:13.126Z")
    private String lastModified;

    @Schema(description = "修改次数", example = "7")
    private Integer modificationCount;

}