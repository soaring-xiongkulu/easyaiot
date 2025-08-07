package com.basiclab.iot.device.dal.dataobject.product_template;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模板 DO
 *
 * @author BasicLab
 */
@TableName("product_template")
@KeySequence("product_template_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductTemplateDO extends BaseDO {

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
     * 产品模版标识
     */
    private String templateCode;
    /**
     * 产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线
     */
    private String templateName;
    /**
     * 状态(字典值：启用  停用)
     */
    private String status;
    /**
     * 产品模型模板描述
     */
    private String remark;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}