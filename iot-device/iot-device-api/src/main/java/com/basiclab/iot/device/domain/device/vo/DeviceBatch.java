package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * (DeviceBatch)实体类
 *
 * @author makejava
 * @since 2025-06-18 14:36:53
 */
@Data
public class DeviceBatch implements Serializable {
    private static final long serialVersionUID = -54159772729593908L;
    /**
     * 主键id
     */
    @ApiModelProperty("主键id")
    private Long id;
    /**
     * 批次号
     */
    @ApiModelProperty("批次号")
    private String batchNumber;
    /**
     * 产品名称
     */
    @ApiModelProperty("产品名称")
    private String productName;
    /**
     * 申请数量
     */
    @ApiModelProperty("申请数量")
    private Integer applyAmount;
    /**
     * 成功数量
     */
    @ApiModelProperty("成功数量")
    private Integer successAmount;
    /**
     * 文件路径
     */
    @ApiModelProperty("文件路径")
    private String fileUrl;
    /**
     * 创建人
     */
    @ApiModelProperty("创建人")
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    private String createBy;
    /**
     * 创建时间
     */
    @ApiModelProperty(value = "创建时间")
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;

}

