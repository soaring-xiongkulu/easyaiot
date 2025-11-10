package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 数据集 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset")
@KeySequence("dataset_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 数据集编码
     */
    private String datasetCode;
    /**
     * 数据集名称
     */
    private String name;
    /**
     * 封面地址
     */
    private String coverPath;
    /**
     * 描述
     */
    private String description;
    /**
     * 数据集类型，0-图片；1-文本
     */
    private Integer datasetType;
    /**
     * 数据集状态：0-待审核；1-审核通过；2-驳回
     */
    private Integer audit;
    /**
     * 审核驳回理由
     */
    private String reason;
    /**
     * 是否已划分数据集[0:否,1:是]
     */
    private Integer isAllocated;
    /**
     * 自动化标注预训练模型服务ID
     */
    private Long modelServiceId;
    /**
     * 是否已生成数据集到Minio[0:否,1:是]
     */
    private Integer isSyncMinio;
    /**
     * 数据集压缩包下载地址
     */
    private String zipUrl;
    /**
     * 图片总数
     */
    @TableField(exist = false)
    private Integer totalImages;
    /**
     * 已标注图片数
     */
    @TableField(exist = false)
    private Integer annotatedImages;

}