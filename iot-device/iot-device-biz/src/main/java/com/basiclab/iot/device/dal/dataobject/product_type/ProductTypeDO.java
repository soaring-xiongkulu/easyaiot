package com.basiclab.iot.device.dal.dataobject.product_type;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品分类 DO
 *
 * @author BasicLab
 */
@TableName("product_type")
@KeySequence("product_type_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductTypeDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 名称
     */
    private String name;
    /**
     * 排序序号
     */
    private Long sort;
    /**
     * 父级ID
     */
    private String parentId;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;

}