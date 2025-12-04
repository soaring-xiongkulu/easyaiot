package com.basiclab.iot.message.common;

import com.basiclab.iot.message.domain.entity.TPushHistory;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.sendlogic.MessageTypeEnum;
import com.basiclab.iot.message.sendlogic.msgsender.*;
import com.basiclab.iot.message.service.PushHistoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

/**
 * 通知发送公共类
 * 支持6种通知方式：短信(阿里云/腾讯云)、邮件、企业微信、HTTP、钉钉、飞书
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
    private FeishuMsgSender feishuMsgSender;

    @Autowired
    private PushHistoryService pushHistoryService;

    /**
     * 消息发送器映射表（优化：使用Map替代switch-case）
     */
    private Map<Integer, Function<String, SendResult>> senderMap;

    /**
     * 初始化发送器映射表
     */
    private void initSenderMap() {
        if (senderMap == null) {
            senderMap = new HashMap<>();
            // 短信：阿里云(1)和腾讯云(2)
            senderMap.put(MessageTypeEnum.ALI_YUN_CODE, aliYunMsgSender::send);
            senderMap.put(MessageTypeEnum.TX_YUN_CODE, txYunMsgSender::send);
            // 邮件(3)
            // 企业微信(4)
            senderMap.put(MessageTypeEnum.WX_CP_CODE, wxCpMsgSender::send);
            // HTTP/webhook(5)
            senderMap.put(MessageTypeEnum.HTTP_CODE, httpMsgSender::send);
            // 钉钉(6)
            senderMap.put(MessageTypeEnum.DING_CODE, dingMsgSender::send);
            // 飞书(7)
            senderMap.put(MessageTypeEnum.FEISHU_CODE, feishuMsgSender::send);
        }
    }

    /**
     * 发送邮件消息
     */
    public SendResult messageMailSend(int msgType, String msgId, String content) {
        SendResult sendResult = mailMsgSender.send(msgId, content);
        addPushHistory(msgType, msgId, sendResult);
        return sendResult;
    }

    /**
     * 发送消息（优化：使用Map替代switch-case）
     */
    public SendResult messageSend(int msgType, String msgId) {
        initSenderMap();
        
        Function<String, SendResult> sender = senderMap.get(msgType);
        if (sender == null) {
            return new SendResult();
        }
        
        SendResult sendResult = sender.apply(msgId);
        addPushHistory(msgType, msgId, sendResult);
        return sendResult;
    }

    /**
     * 添加推送历史记录
     */
    private void addPushHistory(int msgType, String msgId, SendResult sendResult) {
        TPushHistory tPushHistory = new TPushHistory();
        tPushHistory.setMsgId(msgId);
        tPushHistory.setMsgType(msgType);
        tPushHistory.setMsgName(sendResult.getMsgName());
        if (sendResult.isSuccess()) {
            tPushHistory.setResult("成功");
        } else {
            tPushHistory.setResult("失败，失败原因：" + sendResult.getInfo());
        }
        pushHistoryService.add(tPushHistory);
    }
}
