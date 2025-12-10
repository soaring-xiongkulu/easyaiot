package com.basiclab.iot.message.sendlogic.msgmaker;

import com.basiclab.iot.message.domain.entity.TMsgMail;
import com.basiclab.iot.message.mapper.TMsgMailMapper;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * email-消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Component
public class MailMsgMaker {

    @Autowired
    private TMsgMailMapper tMsgMailMapper;


    /**
     * 组织E-Mail消息
     *
     * @param msgId 消息信息
     * @return MailMsg
     */
    public TMsgMail makeMsg(String msgId, String mailContent) {
       TMsgMail tMsgMail = tMsgMailMapper.selectByPrimaryKey(msgId);
       if (tMsgMail == null) {
           throw new RuntimeException("邮件消息不存在: msgId=" + msgId);
       }
       if(StringUtils.isNotEmpty(mailContent)){
           tMsgMail.setContent(mailContent);
       }
        return tMsgMail;
    }
}
