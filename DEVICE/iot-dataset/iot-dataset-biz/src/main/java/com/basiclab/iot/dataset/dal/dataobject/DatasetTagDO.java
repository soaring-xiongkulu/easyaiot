package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 数据集标签 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_tag")
@KeySequence("dataset_tag_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetTagDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 标签名称
     */
    private String name;
    /**
     * 标签颜色
     */
    private String color;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 数据仓ID
     */
    private Long warehouseId;
    /**
     * 描述
     */
    private String description;
    /**
     * 快捷键
     */
    private Integer shortcut;

}