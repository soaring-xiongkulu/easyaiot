package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 标注任务结果 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_task_result")
@KeySequence("dataset_task_result_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetTaskResultDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 数据集图片ID
     */
    private Long datasetImageId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 是否有标注[0:无,1:有]
     */
    private Integer hasAnno;
    /**
     * 标注信息
     */
    private String annos;
    /**
     * 任务类型[0:智能标注,1:人员标注,2:审核]
     */
    private Integer taskType;
    /**
     * 标注或审核的用户id
     */
    private Long userId;
    /**
     * 通过状态[0:待审核,1:通过,2:驳回]
     */
    private Integer passStatus;
    /**
     * 任务ID
     */
    private Long taskId;
    /**
     * 驳回原因
     */
    private String reason;
    /**
     * 是否修改过[0:否,1是]
     */
    private Integer isUpdate;

}