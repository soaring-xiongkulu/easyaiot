package com.basiclab.iot.dataset.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;

/**
 * 图片数据集 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_image")
@KeySequence("dataset_image_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetImageDO extends BaseEntity {

    @TableId
    private Long id;

    @Schema(description = "数据集ID", example = "1569")
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

    @Schema(description = "是否训练集[0:否,1:是]", example = "0")
    private Integer isTrain;

    @Schema(description = "是否验证集[0:否,1:是]", example = "0")
    private Integer isValidation;

    @Schema(description = "是否测试集[0:否,1:是]", example = "0")
    private Integer isTest;

}