package com.basiclab.iot.dataset.domain.dataset.vo;

import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.domain.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;

import static com.basiclab.iot.common.utils.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

/**
 * DatasetImagePageReqVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 图片数据集分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class DatasetImagePageReqVO extends PageParam {

    @Schema(description = "数据集ID", example = "1569")
    private Long datasetId;

    @Schema(description = "图片名称", example = "张三")
    private String name;

    @Schema(description = "图片地址")
    private String path;

    @Schema(description = "最后修改时间", example = "2025-06-24T13:10:13.126Z")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] lastModified;

    @Schema(description = "修改次数", example = "7")
    private Integer modificationCount;

    @Schema(description = "图片宽度")
    private Integer width;

    @Schema(description = "图片高度")
    private Integer heigh;

    @Schema(description = "图片大小")
    private Long size;

    @Schema(description = "视频ID（来源为视频切片）", example = "21383")
    private Long datasetVideoId;

    @Schema(description = "是否标注完成[0:否,1:是]", example = "1")
    @ExcelProperty("是否标注完成[0:否,1:是]")
    private Integer completed;

    @Schema(description = "是否训练集[0:否,1:是]", example = "0")
    private Integer isTrain;

    @Schema(description = "是否验证集[0:否,1:是]", example = "0")
    private Integer isValidation;

    @Schema(description = "是否测试集[0:否,1:是]", example = "0")
    private Integer isTest;

}