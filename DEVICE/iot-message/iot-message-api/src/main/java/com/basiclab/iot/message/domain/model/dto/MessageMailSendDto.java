package com.basiclab.iot.message.domain.model.dto;

import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-07-22
 */
@Data
@Tag(name  ="消息发送")
public class MessageMailSendDto {

    @ApiModelProperty("消息id")
    private String msgId;

    @ApiModelProperty("消息类型")
    private Integer msgType;

    @ApiModelProperty("消息内容")
    private String content;


}
