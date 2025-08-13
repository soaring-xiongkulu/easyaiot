package com.basiclab.iot.device.domain.device.vo;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;

import javax.validation.constraints.NotEmpty;
import java.io.Serializable;
import java.util.List;

/**
 * 在线调试请求参数实体
 * @author EasyAIoT
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Builder
@ApiModel(value = "在线调试请求参数实体", description = "Device Command Request Wrapper Data Structure")
public class CommandWrapperParamReq implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty("设备标识列表")
    private List<String> deviceIdentificationList;

    @ApiModelProperty(value = "产品标识")
    @NotEmpty(message = "产品标识不能为空")
    private String productIdentification;

    @ApiModelProperty(value = "串行命令请求列表")
    private List<CommandIssueRequestParam> serial;

    @ApiModelProperty(value = "并行命令请求列表")
    private List<CommandIssueRequestParam> parallel;
}
