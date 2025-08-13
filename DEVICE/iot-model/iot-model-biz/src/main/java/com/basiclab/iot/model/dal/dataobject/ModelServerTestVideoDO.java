package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型测试视频 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server_test_video")
@KeySequence("model_server_test_video_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerTestVideoDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 测试模型服务ID
     */
    private Long modelServerTestId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 数据集视频ID
     */
    private Long datasetVideoId;
    /**
     * 标注时间
     */
    private LocalDateTime annoTime;
    /**
     * 标注后视频路径
     */
    private String annoVideoPath;
    /**
     * 状态[0:运行中,1:成功,2:失败]
     */
    private Short state;

}