package com.basiclab.iot.message.sendlogic.msgmaker;

public interface IMsgMaker {
    /**
     * 准备(界面字段等)
     */
    void prepare();

    /**
     * 消息加工器接口
     *
     * @param msgId 消息数据
     * @return Object
     */
    Object makeMsg(String msgId);
}
