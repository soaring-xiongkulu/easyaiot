package com.basiclab.iot.dataset.domain.dataset.vo;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.alibaba.excel.annotation.*;

/**
 * DatasetRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 数据集 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "22596")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "数据集编码")
    @ExcelProperty("数据集编码")
    private String datasetCode;

    @Schema(description = "数据集名称", example = "张三")
    @ExcelProperty("数据集名称")
    private String name;

    @Schema(description = "封面地址")
    @ExcelProperty("封面地址")
    private String coverPath;

    @Schema(description = "描述", example = "你猜")
    @ExcelProperty("描述")
    private String description;

    @Schema(description = "数据集类型，0-图片；1-文本", example = "0")
    @ExcelProperty("数据集类型，0-图片；1-文本")
    private Integer datasetType;

    @Schema(description = "数据集状态：0-待审核；1-审核通过；2-驳回")
    @ExcelProperty("数据集状态：0-待审核；1-审核通过；2-驳回")
    private Integer audit;

    @Schema(description = "审核驳回理由", example = "不好")
    @ExcelProperty("审核驳回理由")
    private String reason;

    @Schema(description = "是否已生成数据集到Minio，0-否；1-是", example = "0")
    @ExcelProperty("是否已生成数据集到Minio，0-否；1-是")
    private Integer isSyncMinio;

    @Schema(description = "图片总数")
    private Integer totalImages;

    @Schema(description = "已标注图片数")
    private Integer annotatedImages;

}