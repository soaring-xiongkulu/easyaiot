package com.basiclab.iot.device.dal.dataobject.product_properties;

import lombok.*;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.mybatis.core.dataobject.BaseDO;

/**
 * 产品模型属性 DO
 *
 * @author BasicLab
 */
@TableName("product_properties")
@KeySequence("product_properties_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductPropertiesDO extends BaseDO {

    /**
     * id
     */
    @TableId
    private Long id;
    /**
     * 功能名称
     */
    private String propertyName;
    /**
     * 属性code
     */
    private String propertyCode;
    /**
     * 指示数据类型：取值范围：string、int、decimal（float和double都可以使用此类型）、DateTime、jsonObject上报数据时，复杂类型数据格式如下：	•DateTime:yyyyMMdd’T’HHmmss’Z’如:20151212T121212Z•jsonObject：自定义json结构体，平台不理解只透传
     */
    private String datatype;
    /**
     * 属性描述，不影响实际功能，可配置为空字符串""。
     */
    private String description;
    /**
     * 指示枚举值:如开关状态status可有如下取值enumList : [OPEN,CLOSE]目前本字段是非功能性字段，仅起到描述作用。建议准确定义。
     */
    private String enumlist;
    /**
     * 指示最大值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑小于等于。
     */
    private String max;
    /**
     * 指示字符串长度。仅当dataType为string、DateTime时生效。
     */
    private Long maxlength;
    /**
     * 指示访问模式。R:可读；W:可写；E属性值更改时上报数据取值范围：R、RW、RE、RWE
     */
    private String method;
    /**
     * 指示最小值。支持长度不超过50的数字。仅当dataType为int、decimal时生效，逻辑大于等于。
     */
    private String min;
    /**
     * 指示本条属性是否必填，取值为0或1，默认取值1（必填）。目前本字段是非功能性字段，仅起到描述作用。(字典值link_product_isRequired：0非必填 1必填)
     */
    private Integer required;
    /**
     * 指示步长。
     */
    private Integer step;
    /**
     * 指示单位。支持长度不超过50。	取值根据参数确定，如：	•温度单位：“C”或“K”	•百分比单位：“%”	•压强单位：“Pa”或“kPa”
     */
    private String unit;
    /**
     * 创建者
     */
    private String createBy;
    /**
     * 更新者
     */
    private String updateBy;
    /**
     * 模版code
     */
    private String templateCode;
    /**
     * 产品唯一标识
     */
    private String pid;

}