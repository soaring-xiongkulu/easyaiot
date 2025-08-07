package com.basiclab.iot.device.dal.dataobject.protocol;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 协议信息 DO
 *
 * @author BasicLab
 */
@TableName("protocol")
@KeySequence("protocol_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProtocolDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 应用ID
     */
    private String appId;
    /**
     * 产品标识
     */
    private String pid;
    /**
     * 协议名称
     */
    private String protocolName;
    /**
     * 协议标识
     */
    private String protocolCode;
    /**
     * 协议版本
     */
    private String protocolVersion;
    /**
     * 协议类型 ：mqtt || coap || modbus || http
     */
    private String protocolType;
    /**
     * 协议语言
     */
    private String protocolVoice;
    /**
     * 类名
     */
    private String className;
    /**
     * 文件地址
     */
    private String filePath;
    /**
     * 内容
     */
    private String content;
    /**
     * 状态(字典值：0启用  1停用)
     */
    private String status;
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