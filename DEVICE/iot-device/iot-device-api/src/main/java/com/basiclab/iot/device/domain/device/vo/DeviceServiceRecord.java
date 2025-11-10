package com.basiclab.iot.device.domain.device.vo;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.*;
import lombok.experimental.Accessors;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * 设备服务记录管理
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@ApiModel(value="设备服务记录")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
@Accessors(chain = true)
@Builder
@TableName("device_service_records")
public class DeviceServiceRecord implements Serializable {
    /**
    * id
    */
    @ApiModelProperty(value="id")
    private Long id;

    /**
     * 设备标识
     */
    @ApiModelProperty(value = "设备标识")
    private String deviceIdentification;

    /**
     * 服务标识符
     */
    @ApiModelProperty("服务标识符")
    private String serviceCode;

    /**
     * 命令标识符
     */
    @ApiModelProperty("命令标识符")
    private String commandCode;

    /**
     * 命令名称
     */
    @ApiModelProperty("命令名称")
    private String commandName;

    /**
     * 协议类型 ：mqtt || coap || modbus || http
     */
    @ApiModelProperty(value = "协议类型 ：mqtt || coap || modbus || http")
    private String protocolType;

    /**
     * 消息ID
     */
    @ApiModelProperty(value = "消息ID")
    private String messageId;

    /**
     * topic
     */
    @ApiModelProperty(value = "topic")
    private String topic;

    /**
     * 输入参数
     */
    @ApiModelProperty(value = "设备请求消息")
    private String request;

    /**
     * 内容信息
     */
    @ApiModelProperty(value = "设备响应内容信息")
    private String message;

    /**
     * 状态
     */
    @ApiModelProperty(value = "状态 0.未下发 1.已下发 2.已回复")
    private Integer status;

    /**
     * 响应上报时间
     */
    @ApiModelProperty(value = "响应上报时间")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime reportTime;

    /**
     * 创建时间
     */
    @TableField(value = "create_time", fill = FieldFill.INSERT)
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @ApiModelProperty(value = "创建时间")
    private LocalDateTime createTime;

    private static final long serialVersionUID = 1L;


    public enum statusEnum {
        /**
         * 未下发
         */
        UNSENT(0),
        /**
         * 已发送
         */
        SENT(1),
        /**
         * 已回复
         */
        Replied(2)
        ;

        private Integer statusNum;

        statusEnum(Integer statusNum) {
            this.statusNum = statusNum;
        }

        public Integer getStatusNum() {
            return statusNum;
        }
    }
}