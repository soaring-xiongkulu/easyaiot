package com.basiclab.iot.device.domain.device.qo;

import com.alibaba.excel.annotation.ExcelProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.io.Serializable;

/**
 * @author zhangzhixiang on 2024/7/31
 */
@Data
@ApiModel(value = "DeviceAlarmQo对象", description = "DeviceAlarmQo对象")
public class DeviceAlarmQo implements Serializable {

    private static final long serialVersionUID = -2247287287146748992L;
    /**
     * 应用名
     */
    @ApiModelProperty(value = "应用名")
    private String app;
    /**
     * 流id
     */
    @ApiModelProperty(value = "流id")
    private String stream;
    /**
     * 桶名称
     */
    @ApiModelProperty(value = "桶名称")
    private String bucketName;
    /**
     * 对象前缀
     */
    @ApiModelProperty(value = "对象前缀")
    private String prefix;
    /**
     * 对象key
     */
    @ApiModelProperty(value = "对象key")
    private String objectKey;
    /**
     * 告警内容
     */
    @ApiModelProperty(value = "告警内容")
    private String content;
    /**
     * 告警时间
     */
    @ApiModelProperty(value = "告警时间")
    private String timestamp;
}