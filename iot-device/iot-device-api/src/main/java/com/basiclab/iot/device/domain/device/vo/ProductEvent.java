package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * (ProductEvent)实体类
 *
 * @author makejava
 * @since 2025-06-07 11:23:40
 */
@ApiModel(value = "产品事件模型")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class ProductEvent implements Serializable {
    private static final long serialVersionUID = 214934116551554711L;
    /**
     * 主键
     */
    private Long id;
    /**
     * 事件名称
     */
    @ApiModelProperty("事件名称")
    private String eventName;
    /**
     * 事件标识
     */
    @ApiModelProperty("事件标识")
    private String eventCode;
    /**
     * 事件类型。
     * INFO_EVENT_TYPE：信息。
     * ALERT_EVENT_TYPE：告警。
     * ERROR_EVENT_TYPE：故障
     */
    @ApiModelProperty("事件类型 INFO_EVENT_TYPE：信息。 ALERT_EVENT_TYPE：告警。 ERROR_EVENT_TYPE：故障")
    private String eventType;
    /**
     * 产品模版标识
     */
    @ApiModelProperty("产品模版标识")
    private String templateIdentification;
    /**
     * 产品标识
     */
    @ApiModelProperty("产品标识")
    private String productIdentification;
    /**
     * 状态(字典值：0启用  1停用)
     */
    @ApiModelProperty("状态(字典值：0启用  1停用)")
    private String status;
    /**
     * 描述
     */
    @ApiModelProperty("描述")
    private String description;
    /**
     * 创建者
     */
    @ApiModelProperty("创建者")
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    private String createBy;
    /**
     * 创建时间
     */
    @ApiModelProperty("创建时间")
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;
    /**
     * 更新者
     */
    @ApiModelProperty("更新者")
    @TableField(value = "update_by", fill = FieldFill.INSERT_UPDATE)
    private String updateBy;
    /**
     * 更新时间
     */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty("更新时间")
    private LocalDateTime updateTime;

}

