package com.basiclab.iot.message.domain.model.vo;

import com.basiclab.iot.message.domain.entity.*;
import lombok.Data;

import java.util.List;

/**
 * 消息准备实体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2023-07-19
 */
@Data
public class MessagePrepareVO {
    private TMsgMail t_Msg_Mail;

    private TMsgHttp t_Msg_Http;

    private TMsgDing t_Msg_Ding;

    private TMsgWxCp t_Msg_Wx_Cp;

    private TMsgSms t_Msg_Sms;

    private TMsgFeishu t_Msg_Feishu;

    private List<TTemplateData> templateDataList;

    private int msgType;

    private String msgName;
}
