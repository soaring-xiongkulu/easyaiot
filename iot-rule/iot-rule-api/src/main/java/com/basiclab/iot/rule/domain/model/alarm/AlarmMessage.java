package com.basiclab.iot.rule.domain.model.alarm;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;

/**
 * @author EasyAIoT
 * @desc 告警通知消息
 * @created 2025-07-18
 */
@Data
@ApiModel("告警通知消息")
public class AlarmMessage {

    @ApiModelProperty("告警相关信息")
    private AlarmInfo alarmInfo;
    @ApiModelProperty("告警消息通知策略")
    private List<NotifyAction> notifyAction;
    @Data
    @ApiModel("告警消息")
    public static class AlarmInfo {
        @ApiModelProperty("产品标识")
        private String productIdentification;
        @ApiModelProperty("设备标识  如果设备标识为ALL 那么通过产品标识处理")
        private String deviceIdentification;
        @ApiModelProperty("告警水平")
        private String alarmLevel;
        @ApiModelProperty("告警所需属性编码集合")
        private List<String> propertyCodeList;
        @ApiModelProperty("告警名称")
        private String alarmName;
        @ApiModelProperty("消息内容")
        private String content;
        @ApiModelProperty("处理状态")
        private String handledStatus;
    }

    @Data
    @ApiModel("通知消息")
    public static class NotifyAction {
        @ApiModelProperty("消息类型  1 阿里云消息  2腾讯云消息  3 邮件消息发送  4 微信企业号消息  5 http消息发送  6 钉钉消息发送")
        private int msgType;
        @ApiModelProperty("消息id")
        private String msgId;
        @ApiModelProperty("消息消息内容 邮件内容，当且只当msgType=3时需要设置")
        private String content;
    }

}
