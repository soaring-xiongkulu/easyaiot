package com.basiclab.iot.tdengine.domain.query;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import org.springframework.validation.annotation.Validated;

import javax.validation.constraints.NotNull;

/**
 * 设备时序数据查询请求
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ApiModel("设备时序数据查询请求")
@Data
@Validated
public class DeviceTimeSeriesQueryRequest {
    
    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识", required = true)
    @NotNull(message = "设备标识不能为空")
    private String deviceIdentification;
    
    /**
     * 超级表类型
     * PROPERTY_UPSTREAM_REPORT: 属性上报
     * EVENT_UPSTREAM_REPORT: 事件上报
     * SERVICE_UPSTREAM_INVOKE_RESPONSE: 服务调用响应
     * DEVICE_TAG_UPSTREAM_REPORT: 设备标签上报
     * SHADOW_UPSTREAM_REPORT: 影子上报
     * PROPERTY_UPSTREAM_DESIRED_SET_ACK: 属性期望值设置确认
     * PROPERTY_UPSTREAM_DESIRED_QUERY_RESPONSE: 属性期望值查询响应
     */
    @ApiModelProperty(value = "超级表类型", required = true)
    @NotNull(message = "超级表类型不能为空")
    private String superTableType;
    
    /**
     * 标识符（用于事件和服务）
     */
    @ApiModelProperty(value = "标识符（用于事件和服务）")
    private String identifier;
    
    /**
     * 开始时间（时间戳，毫秒）
     */
    @ApiModelProperty(value = "开始时间（时间戳，毫秒）")
    private Long startTime;
    
    /**
     * 结束时间（时间戳，毫秒）
     */
    @ApiModelProperty(value = "结束时间（时间戳，毫秒）")
    private Long endTime;
    
    /**
     * 分页页码
     */
    @ApiModelProperty(value = "分页页码", example = "1")
    private Integer pageNum = 1;
    
    /**
     * 每页大小
     */
    @ApiModelProperty(value = "每页大小", example = "10")
    private Integer pageSize = 10;
    
    /**
     * 数据库名（内部使用，不需要前端传入）
     */
    @ApiModelProperty(value = "数据库名", hidden = true)
    private String tdDatabaseName;
    
    /**
     * 超级表名（内部使用，与 superTableType 对应）
     */
    @ApiModelProperty(value = "超级表名", hidden = true)
    private String superTableName;
}

