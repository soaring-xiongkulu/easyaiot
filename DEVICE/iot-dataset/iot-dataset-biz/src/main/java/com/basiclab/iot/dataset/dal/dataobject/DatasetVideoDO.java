package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 视频数据集 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_video")
@KeySequence("dataset_video_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetVideoDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 视频地址
     */
    private String videoPath;
    /**
     * 视频名称
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

}