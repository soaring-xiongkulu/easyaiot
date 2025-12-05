package com.basiclab.iot.message.controller;


import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.domain.model.dto.MessageMailSendDto;
import com.basiclab.iot.message.common.MessageSendCommon;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

/**
 * 通知发送controller
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@RestController
@RequestMapping("/message")
@Tag(name  ="通知发送")
public class MessageSendController {

    @Autowired
    private MessageSendCommon messageSendCommon;

    @PostMapping("/send")
    @ApiOperation("消息发送")
    public SendResult send(@RequestParam int msgType, @RequestParam String msgId){
        if(msgType == 3){
            return messageSendCommon.messageMailSend(msgType,msgId,"");
        }
        return messageSendCommon.messageSend(msgType, msgId);
    }



    @PostMapping("/messageMailSend")
    @ApiOperation("邮件消息发送")
    public SendResult messageMailSend(@RequestBody MessageMailSendDto messageMailSendDto){
        return messageSendCommon.messageMailSend(messageMailSendDto.getMsgType(),messageMailSendDto.getMsgId(),messageMailSendDto.getContent());
    }

    @PostMapping("/messageSend")
    @ApiOperation("消息发送信息")
    public SendResult messageSend(@RequestBody MessageMailSendDto messageMailSendDto){
        // 如果传递了完整的HTTP参数，使用新方法直接发送
        if (messageMailSendDto.getMsgType() != null && messageMailSendDto.getMsgType() == 5) {
            // HTTP/Webhook 类型，检查是否传递了完整的HTTP参数
            if (messageMailSendDto.getMethod() != null && messageMailSendDto.getUrl() != null) {
                return messageSendCommon.messageSendWithParams(messageMailSendDto);
            }
        }
        // 其他情况或未传递完整参数时，使用原有方法（从数据库读取）
        return messageSendCommon.messageSend(messageMailSendDto.getMsgType(), messageMailSendDto.getMsgId());
    }


}
