package com.basiclab.iot.device.dal.dataobject.product_event;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模型事件 DO
 *
 * @author BasicLab
 */
@TableName("product_event")
@KeySequence("product_event_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductEventDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 事件名称
     */
    private String eventName;
    /**
     * 事件code
     */
    private String eventCode;
    /**
     * 事件类型。	INFO_EVENT_TYPE：信息。	ALERT_EVENT_TYPE：告警。	ERROR_EVENT_TYPE：故障
     */
    private String eventType;
    /**
     * 模板code
     */
    private String templateCode;
    /**
     * 产品唯一标识
     */
    private String pid;
    /**
     * 状态(字典值：0启用  1停用)
     */
    private String enabledStatus;
    /**
     * 描述
     */
    private String description;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}