package com.basiclab.iot.dataset.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 标注任务用户 DO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("dataset_task_user")
@KeySequence("dataset_task_user_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetTaskUserDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 任务ID
     */
    private Long taskId;
    /**
     * 标注用户ID
     */
    private Long userId;
    /**
     * 审核用户ID
     */
    private Long auditUserId;

}