package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 标注任务 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_task")
@KeySequence("dataset_task_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetTaskDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 任务名称
     */
    private String name;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 数据范围[0:全部,1:无标注,2:有标注]
     */
    private Integer dataRange;
    /**
     * 计划标注数量
     */
    private Integer plannedQuantity;
    /**
     * 已标注数量
     */
    private Integer markedQuantity;
    /**
     * 新标签入库[0:否,1:是]
     */
    private Integer newLabel;
    /**
     * 完成状态[0:未完成,1:已完成]
     */
    private Integer finishStatus;
    /**
     * 完成时间
     */
    private LocalDateTime finishTime;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 模型服务ID
     */
    private Long modelServeId;
    /**
     * 是否停止[0:否,1:是]
     */
    private Integer isStop;
    /**
     * 任务类型[0:智能标注,1:人员标注,2:审核]
     */
    private Integer taskType;
    /**
     * 截止时间(人员或审核)
     */
    private LocalDateTime endTime;
    /**
     * 无目标数量
     */
    private Integer notTargetCount;

}