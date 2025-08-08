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
* @description: ${description}
* @packagename: com.basiclab.iot.device.domain.device.vo.entity
* @author EasyIoT
* @date: 2025-11-18 20:36
**/

/**
 * 产品模板
 * @author EasyAIoT
 */
@ApiModel(value = "产品模板")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
public class ProductTemplate implements Serializable {
    /**
     * id
     */
    @ApiModelProperty(value = "id")
    private Long id;

    /**
     * 应用ID
     */
    @ApiModelProperty(value = "应用ID")
    private String appId;

    /**
     * 产品模版标识
     */
    @ApiModelProperty(value = "产品模版标识")
    private String templateIdentification;

    /**
     * 产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线
     */
    @ApiModelProperty(value = "产品模板名称:自定义，支持中文、英文大小写、数字、下划线和中划线")
    private String templateName;

    /**
     * 状态(字典值：启用  停用)
     */
    @ApiModelProperty(value = "状态(字典值：启用  停用)")
    private String status;

    /**
     * 产品模型模板描述
     */
    @ApiModelProperty(value = "产品模型模板描述")
    private String remark;

    /**
     * 创建者
     */
    @ApiModelProperty(value = "创建者")
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    private String createBy;

    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;

    /**
     * 更新者
     */
    @ApiModelProperty(value = "更新者")
    @TableField(value = "update_by", fill = FieldFill.INSERT_UPDATE)
    private String updateBy;

    /**
     * 更新时间
     */
    @ApiModelProperty(value = "更新时间")
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateTime;

    private static final long serialVersionUID = 1L;
}