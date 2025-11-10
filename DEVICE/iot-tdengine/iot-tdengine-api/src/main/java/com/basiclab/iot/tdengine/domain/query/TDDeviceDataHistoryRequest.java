package com.basiclab.iot.tdengine.domain.query;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotNull;


/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ApiModel("查看设备历史数据请求实体")
@Data
@Validated
public class TDDeviceDataHistoryRequest {
    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识")
    @NotNull
    private String deviceIdentification;
    /**
     * 标识
     */
    @ApiModelProperty(value = "标识")
    private String identifier;
    /**
     * 方法类型 properties:属性 service:服务 event:事件
      */
    @ApiModelProperty(value = "方法类型 properties:属性 service:服务 event:事件", hidden = true)
    private String functionType;

    /**
     * 开始时间
     */
    @ApiModelProperty(value = "开始时间")
    @NotNull
//    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private long startTime;

    /**
     * 结束时间
     */
    @ApiModelProperty(value = "结束时间")
    @NotNull
//    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private long endTime;
    /**
     * 数据库名
     */
    @ApiModelProperty(value = "数据库名", hidden = true)
    private String tdDatabaseName;
    /**
     * 超级表名
     */
    @ApiModelProperty(value = "超级表名", hidden = true)
    private String tdSuperTableName;


}
