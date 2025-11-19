package com.basiclab.iot.message.sendlogic.msgmaker;


import com.basiclab.iot.message.sendlogic.MessageTypeEnum;

/**
 * 消息加工器工厂类
 */
public class MsgMakerFactory {



    /**
     * 获取消息加工器
     *
     * @return IMsgMaker
     */
    public static IMsgMaker getMsgMaker(int msgType) {
        IMsgMaker iMsgMaker = null;
        switch (msgType) {
            case MessageTypeEnum.ALI_YUN_CODE:
                iMsgMaker = new AliyunMsgMaker();
                break;
            case MessageTypeEnum.TX_YUN_CODE:
                iMsgMaker = new TxYunMsgMaker();
                break;
            case MessageTypeEnum.WX_CP_CODE:
                iMsgMaker = new WxCpMsgMaker();
                break;
            case MessageTypeEnum.HTTP_CODE:
                iMsgMaker = new HttpMsgMaker();
                break;
            case MessageTypeEnum.DING_CODE:
                iMsgMaker = new DingMsgMaker();
                break;
            default:
        }
        return iMsgMaker;
    }
}
