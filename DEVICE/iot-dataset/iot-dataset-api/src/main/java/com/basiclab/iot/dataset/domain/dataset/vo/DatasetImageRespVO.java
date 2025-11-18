package com.basiclab.iot.dataset.domain.dataset.vo;

import com.alibaba.excel.annotation.ExcelIgnoreUnannotated;
import com.alibaba.excel.annotation.ExcelProperty;
import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * DatasetImageRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - 图片数据集 Response VO")
@Data
@ExcelIgnoreUnannotated
public class DatasetImageRespVO extends BaseEntity {

    @Schema(description = "主键ID", example = "17489")
    @ExcelProperty("主键ID")
    private Long id;

    @Schema(description = "数据集ID", example = "1569")
    @ExcelProperty("数据集ID")
    private Long datasetId;

    @Schema(description = "图片名称", example = "张三")
    @ExcelProperty("图片名称")
    private String name;

    @Schema(description = "图片地址")
    @ExcelProperty("图片地址")
    private String path;

    @Schema(description = "标注信息，JSON格式")
    @ExcelProperty("标注信息，JSON格式")
    private String annotations;

    @Schema(description = "最后修改时间")
    @ExcelProperty("最后修改时间")
    private LocalDateTime lastModified;

    @Schema(description = "图片宽度")
    @ExcelProperty("图片宽度")
    private Integer width;

    @Schema(description = "图片高度")
    @ExcelProperty("图片高度")
    private Integer heigh;

    @Schema(description = "图片大小")
    @ExcelProperty("图片大小")
    private Long size;

    @Schema(description = "视频ID（来源为视频切片）", example = "21383")
    @ExcelProperty("视频ID（来源为视频切片）")
    private Long datasetVideoId;

    @Schema(description = "修改次数", example = "1586")
    @ExcelProperty("修改次数")
    private Integer modificationCount;

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