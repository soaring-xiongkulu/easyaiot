package com.basiclab.iot.dataset.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

/**
 * 视频流帧捕获任务 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_frame_task")
@KeySequence("dataset_frame_task_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetFrameTaskDO extends BaseEntity {

    /**
     * 主键id
     */
    @TableId
    private Long id;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 任务名称
     */
    private String taskName;
    /**
     * 任务编码
     */
    private String taskCode;
    /**
     * 任务类型[0:实时流抽帧,1:GB28181流抽帧]
     */
    private Short taskType;
    /**
     * 通道ID
     */
    private String channelId;
    /**
     * 设备ID
     */
    private String deviceId;
    /**
     * RTMP播放流地址
     */
    private String rtmpUrl;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 创建人
     */
    private String updateBy;

}