package com.basiclab.iot.message.sendlogic.msgsender;


import com.github.qcloudsms.SmsSingleSender;
import com.github.qcloudsms.SmsSingleSenderResult;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgSms;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TMsgSmsMapper;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.sendlogic.msgmaker.TxYunMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * 腾讯云模板短信发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-19
 */
@Slf4j
@Component
public class TxYunMsgSender implements IMsgSender {

    @Autowired
    private TxYunMsgMaker txYunMsgMaker;

    @Autowired
    private TMsgSmsMapper tMsgSmsMapper;

    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;


    @Override
    public SendResult send(String msgId) {
        log.info("腾讯云发送开始 params is:"+msgId);
        SmsSingleSender smsSingleSender = getTxYunSender();
        SendResult sendResult = new SendResult();
        try {
            TMsgSms tMsgSms = tMsgSmsMapper.selectByPrimaryKey(msgId);
            sendResult.setMsgName(tMsgSms.getMsgName());
            MessageConfig messageConfig = messageConfigService.queryByMsgType(2);
            Map<String, Object> configMap = messageConfig.getConfigurationMap();
            int templateId = Integer.parseInt(tMsgSms.getTemplateId());
            String smsSign = (String) configMap.get("txyunSign");
            String[] params = txYunMsgMaker.makeMsg(msgId);
//            String telNum = tMsgSms.getPreviewUser();
            List<String> previewUsers = new ArrayList<>();
            String userGroupId = tMsgSms.getUserGroupId();
            if(StringUtils.isNotEmpty(userGroupId)){
                String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
                List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
                previewUsers  = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
            }
            SmsSingleSenderResult result = new SmsSingleSenderResult();
            for(String telNum : CollectionUtils.emptyIfNull(previewUsers)) {
                result = smsSingleSender.sendWithParam("86", telNum,
                        templateId, params, smsSign, "", "");
            }
            if (result.result == 0) {
                sendResult.setSuccess(true);
            } else {
                sendResult.setSuccess(false);
                sendResult.setInfo(result.toString());
            }

        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(ExceptionUtils.getStackTrace(e));
        }

        return sendResult;
    }

    @Override
    public SendResult asyncSend(String[] msgData) {
        return null;
    }

    /**
     * 获取腾讯云短信发送客户端
     *
     * @return SmsSingleSender
     */
    private SmsSingleSender getTxYunSender() {
        SmsSingleSender smsSingleSender = null;
        MessageConfig messageConfig = messageConfigService.queryByMsgType(2);
        Map<String, Object> configMap = messageConfig.getConfigurationMap();
        if (smsSingleSender == null) {
            synchronized (TxYunMsgSender.class) {
                if (smsSingleSender == null) {
                    //先注释，后续从数据库对应表中查询
                    String txyunAppId = (String) configMap.get("txyunAppId");
                    String txyunAppKey = (String) configMap.get("txyunAppKey");

                    smsSingleSender = new SmsSingleSender(Integer.parseInt(txyunAppId), txyunAppKey);
                }
            }
        }
        return smsSingleSender;
    }
}
