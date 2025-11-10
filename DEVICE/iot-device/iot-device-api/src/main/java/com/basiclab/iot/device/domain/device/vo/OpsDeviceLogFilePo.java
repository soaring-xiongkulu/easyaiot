package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.domain.BaseEntity;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-06-03
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_log_file")
@ApiModel(value = "OpsDeviceLogFilePo对象", description = "设备日志文件")
public class OpsDeviceLogFilePo extends BaseEntity implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "id", type = IdType.AUTO)
    private Long id;

    @ApiModelProperty(value = "设备唯一ID")
    @TableField("device_identification")
    private String deviceIdentification;

    @ApiModelProperty(value = "应用编码[OS-设备OS]")
    @TableField("app_code")
    private String appCode;

    @ApiModelProperty(value = "功能编码")
    @TableField("function_code")
    private String functionCode;

    @ApiModelProperty(value = "功能名称")
    @TableField("function_name")
    private String functionName;

    @ApiModelProperty(value = "文件地址")
    @TableField("file_url")
    private String fileUrl;

    @ApiModelProperty(value = "上传时间")
    @TableField("upload_time")
    private LocalDateTime uploadTime;

    @ApiModelProperty(value = "文件原始名称")
    @TableField("file_name")
    private String fileName;

    @ApiModelProperty(value = "文件大小(单位KB)")
    @TableField("file_size")
    private Integer fileSize;

    @ApiModelProperty(value = "备注")
    @TableField("remark")
    private String remark;

    @ApiModelProperty(value = "状态[0:成功, 1:未开始, 2:上传中, 3:失败]")
    @TableField("status")
    private Integer status;


}
