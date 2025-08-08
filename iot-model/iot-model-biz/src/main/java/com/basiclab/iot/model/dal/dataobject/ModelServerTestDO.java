package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型测试服务 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server_test")
@KeySequence("model_server_test_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerTestDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 模型服务ID
     */
    private Long modelServeId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 测试模型服务名称
     */
    private String name;
    /**
     * 测试模型服务类型[0:图片测试,1:视频测试]
     */
    private Short type;
    /**
     * 计划标注数量
     */
    private Integer plannedQuantity;
    /**
     * 已经标注数量
     */
    private Integer markedQuantity;
    /**
     * 无目标数量
     */
    private Integer notTargetCount;
    /**
     * 完成时间
     */
    private LocalDateTime finishTime;
    /**
     * 服务状态[0:进行中,1:成功,2:失败]
     */
    private Short state;
    /**
     * 描述
     */
    private String description;

}