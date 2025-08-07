package com.basiclab.iot.device.dal.dataobject.product_services;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模型服务 DO
 *
 * @author BasicLab
 */
@TableName("product_services")
@KeySequence("product_services_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductServicesDO extends BaseDO {

    /**
     * 服务id
     */
    @TableId
    private Long id;
    /**
     * 服务编码:支持英文大小写、数字、下划线和中划线
     */
    private String serviceCode;
    /**
     * 服务名称
     */
    private String serviceName;
    /**
     * 产品模版标识
     */
    private String templateCode;
    /**
     * 产品标识
     */
    private String pid;
    /**
     * 状态(字典值：0启用  1停用)
     */
    private String status;
    /**
     * 服务的描述信息:文本描述，不影响实际功能，可配置为空字符串""。	
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