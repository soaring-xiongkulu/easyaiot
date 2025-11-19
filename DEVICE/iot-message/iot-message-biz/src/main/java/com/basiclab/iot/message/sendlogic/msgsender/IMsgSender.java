package com.basiclab.iot.message.sendlogic.msgsender;

import com.basiclab.iot.message.domain.model.SendResult;

/**
 * 消息发送器接口
 */
public interface IMsgSender {

    /**
     * 发送消息
     *
     * @param msgId 消息Id
     */
    SendResult send(String msgId);

    /**
     * 异步发送消息
     *
     * @param msgData 消息数据
     */
    SendResult asyncSend(String[] msgData);
}
