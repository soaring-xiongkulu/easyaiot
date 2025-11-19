package com.basiclab.iot.message.factory;

import com.basiclab.iot.message.RemoteMessageSendService;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.domain.model.dto.MessageMailSendDto;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-07-22
 */
@Component
@Slf4j
public class RemoteMessageSendFactory  implements FallbackFactory<RemoteMessageSendService> {


    @Override
    public RemoteMessageSendService create(Throwable cause) {

        log.error("消息通知管理服务调用失败:{}", cause.getMessage());
        return new RemoteMessageSendService() {

            @Override
            public SendResult send(int msgType, String msgId) {
                return SendResult.builder()
                        .success(false)
                        .msgName("发送消息失败")
                        .info("消息类型:" + msgType + "消息id:" + msgId )
                        .build();
            }

            @Override
            public SendResult messageMailSend(MessageMailSendDto messageMailSendDto) {
                return SendResult.builder()
                        .success(false)
                        .msgName("发送消息失败")
                        .info("消息类型:" + messageMailSendDto.getMsgType() + "消息id:" + messageMailSendDto.getMsgId() + "消息内容:" + messageMailSendDto.getContent() )
                        .build();
            }

            @Override
            public SendResult messageSend(MessageMailSendDto messageMailSendDto) {
                return SendResult.builder()
                        .success(false)
                        .msgName("发送消息失败")
                        .info("消息类型:" + messageMailSendDto.getMsgType() + "消息id:" + messageMailSendDto.getMsgId())
                        .build();
            }
        };
    }



}
