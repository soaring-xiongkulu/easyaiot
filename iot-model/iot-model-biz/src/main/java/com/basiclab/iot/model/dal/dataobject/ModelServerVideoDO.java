package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型服务视频 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server_video")
@KeySequence("model_server_video_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerVideoDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 模型服务ID
     */
    private Long modelServerId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 视频地址
     */
    private String videoPath;
    /**
     * 标注视频地址
     */
    private String annoVideoPath;
    /**
     * 封面地址
     */
    private String coverPath;
    /**
     * 描述
     */
    private String description;
    /**
     * 视频分辨率
     */
    private String videoResolution;
    /**
     * 视频时长
     */
    private Integer duration;
    /**
     * 视频后缀
     */
    private String suffix;
    /**
     * 视频文件大小
     */
    private Long fileSize;

}