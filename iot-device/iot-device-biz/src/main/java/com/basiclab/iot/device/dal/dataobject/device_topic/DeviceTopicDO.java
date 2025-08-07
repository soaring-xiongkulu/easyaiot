package com.basiclab.iot.device.dal.dataobject.device_topic;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 设备Topic数据 DO
 *
 * @author BasicLab
 */
@TableName("device_topic")
@KeySequence("device_topic_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DeviceTopicDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 设备标识
     */
    private String did;
    /**
     * 类型(0:基础Topic,1:自定义Topic)
     */
    private String type;
    /**
     * topic
     */
    private String topic;
    /**
     * 发布者
     */
    private String publisher;
    /**
     * 订阅者
     */
    private String subscriber;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;
    /**
     * 备注
     */
    private String remark;

}