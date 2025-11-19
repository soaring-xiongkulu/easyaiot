package com.basiclab.iot.message;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.message.domain.model.dto.MessageMailSendDto;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.factory.RemoteMessageSendFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-07-22
 */
@FeignClient(contextId = "RemoteMessageSendService", value = ServiceNameConstants.IOT_MESSAGE, fallbackFactory = RemoteMessageSendFactory.class)
public interface RemoteMessageSendService {

    /**
     * 发送消息
     * @param msgType
     * @param msgId
     * @return
     */
    @PostMapping("/message/send")
    public SendResult send(@RequestParam("msgType") int msgType, @RequestParam("msgId") String msgId);


    /**
     * 发送邮件消息
     * @param messageMailSendDto
     * @return
     */
    @PostMapping("/message/messageMailSend")
    public SendResult messageMailSend(@RequestBody MessageMailSendDto messageMailSendDto);

    /**
     * 发送消息
     * @param messageMailSendDto
     * @return
     */
    @PostMapping("/message/messageSend")
    public SendResult messageSend(@RequestBody MessageMailSendDto messageMailSendDto);

}
