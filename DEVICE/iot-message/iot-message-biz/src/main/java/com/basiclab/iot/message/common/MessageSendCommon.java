package com.basiclab.iot.message.common;


import com.basiclab.iot.message.domain.entity.TPushHistory;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.sendlogic.msgsender.*;
import com.basiclab.iot.message.service.PushHistoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 通知发送公共类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Component
public class MessageSendCommon {
    @Autowired
    private AliYunMsgSender aliYunMsgSender;

    @Autowired
    private TxYunMsgSender txYunMsgSender;

    @Autowired
    private MailMsgSender mailMsgSender;

    @Autowired
    private WxCpMsgSender wxCpMsgSender;

    @Autowired
    private HttpMsgSender httpMsgSender;

    @Autowired
    private DingMsgSender dingMsgSender;

    @Autowired
    private PushHistoryService pushHistoryService;

    public SendResult messageMailSend(int msgType, String msgId, String content) {
        SendResult sendResult = mailMsgSender.send(msgId,content);
        addPushHistory(msgType, msgId, sendResult);
        return sendResult;
    }

    public SendResult messageSend(int msgType, String msgId) {
        switch (msgType){
            case 1 :
                SendResult sendResult1 = aliYunMsgSender.send(msgId);
                // 新增推送历史记录
                addPushHistory(msgType, msgId, sendResult1);
                return sendResult1;
            case 2 :
                SendResult sendResult2 = txYunMsgSender.send(msgId);
                addPushHistory(msgType, msgId, sendResult2);
                return sendResult2;
            case 4 :
                SendResult sendResult4 = wxCpMsgSender.send(msgId);
                addPushHistory(msgType, msgId, sendResult4);
                return sendResult4;
            case 5 :
                SendResult sendResult5 = httpMsgSender.send(msgId);
                addPushHistory(msgType, msgId, sendResult5);
                return sendResult5;
            case 6 :
                SendResult sendResult6 = dingMsgSender.send(msgId);
                addPushHistory(msgType, msgId, sendResult6);
                return sendResult6;
            default :
                return new SendResult();
        }
    }

    private void addPushHistory(int msgType, String msgId, SendResult sendResult1) {
        TPushHistory tPushHistory = new TPushHistory();
        tPushHistory.setMsgId(msgId);
        tPushHistory.setMsgType(msgType);
        tPushHistory.setMsgName(sendResult1.getMsgName());
        if(sendResult1.isSuccess()){
            tPushHistory.setResult("成功");
        } else{
            tPushHistory.setResult("失败"+"，失败原因："+ sendResult1.getInfo());
        }
        pushHistoryService.add(tPushHistory);
    }
}
