package com.basiclab.iot.rule.domain;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * @author EasyAIoT
 * @desc
 * @created 2025-07-18
 */
@ApiModel(value = "告警信息表")
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AlarmRecord {

//    @Tolerate
//    public AlarmRecord() {
//    }

    @ApiModelProperty(value="主键id")
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 应用id
     */
    @ApiModelProperty(value="应用id")
    private String appId;

    /**
     * 处理状态
     */
    @ApiModelProperty(value="处理状态  0 未处理  1 处理中  2 处理完成")
    private Integer handledStatus;

    /**
     * 告警名称
     */
    @ApiModelProperty(value="告警名称")
    private String alarmName;

    /**
     * 告警级别
     */
    @ApiModelProperty(value="告警级别   low  低级   mid 中级   high 高级")
    private String alarmLevel;

    /**
     * 告警标识
     */
    @ApiModelProperty(value="告警标识")
    private String alarmIdentification;

    /**
     * 告警内容
     */
    @ApiModelProperty(value="告警内容")
    private String content;


    /**
     * 告警实时数据
     *      {
     *          "temprature":"27.2"
     *      }
     */
    @ApiModelProperty(value="告警实时数据 json")
    private String alarmData;

    /**
     * 解决方式记录
     */
    @ApiModelProperty(value="解决方式记录")
    private String resolutionNotes;

    /**
     * 处理时间
     */
    @ApiModelProperty(value = "处理时间")
    private LocalDateTime handledTime;


    /** 创建者 */
    @TableField(value = "create_by", fill = FieldFill.INSERT)
    @ApiModelProperty(value = "创建者")
    private String createBy;

    /** 创建时间 */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createTime;

    /** 更新者 */
    @TableField(value = "update_by", fill = FieldFill.INSERT_UPDATE)
    @ApiModelProperty(value = "更新时间")
    private String updateBy;

    /** 更新时间 */
    @TableField(value = "update_time", fill = FieldFill.INSERT_UPDATE)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty(value = "更新时间")
    private LocalDateTime updateTime;



}
