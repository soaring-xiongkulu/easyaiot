package com.basiclab.iot.message.sendlogic.msgsender;


import com.aliyuncs.DefaultAcsClient;
import com.aliyuncs.IAcsClient;
import com.aliyuncs.dysmsapi.model.v20170525.SendSmsRequest;
import com.aliyuncs.dysmsapi.model.v20170525.SendSmsResponse;
import com.aliyuncs.http.HttpClientConfig;
import com.aliyuncs.profile.DefaultProfile;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgSms;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TMsgSmsMapper;
import com.basiclab.iot.message.sendlogic.msgmaker.AliyunMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * 阿里云模板短信发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Slf4j
@Component
public class AliYunMsgSender implements IMsgSender {
    /**
     * 阿里云短信client
     */

    @Autowired
    private AliyunMsgMaker aliyunMsgMaker;

    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private TMsgSmsMapper tMsgSmsMapper;


    @Override
    public SendResult send(String msgId) {
        SendResult sendResult = new SendResult();
        IAcsClient iAcsClient = getAliyunIAcsClient();

        try {
            //初始化acsClient,暂不支持region化
            SendSmsRequest sendSmsRequest = aliyunMsgMaker.makeMsg(msgId);
            TMsgSms tMsgSms = tMsgSmsMapper.selectByPrimaryKey(msgId);
            sendResult.setMsgName(tMsgSms.getMsgName());
            sendSmsRequest.setPhoneNumbers(sendSmsRequest.getPhoneNumbers());
            SendSmsResponse response = iAcsClient.getAcsResponse(sendSmsRequest);
            if (response.getCode() != null && "OK".equals(response.getCode())) {
                sendResult.setSuccess(true);
            } else {
                sendResult.setSuccess(false);
                sendResult.setInfo(response.getMessage() + "；ErrorCode:" + response.getCode());
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
     * 获取阿里云短信发送客户端
     *
     * @return IAcsClient
     */
    private IAcsClient getAliyunIAcsClient() {
        IAcsClient iAcsClient = null;
        MessageConfig messageConfig = messageConfigService.queryByMsgType(1);
        Map<String,Object> configMap = messageConfig.getConfigurationMap();
        if (iAcsClient == null) {
            synchronized (AliYunMsgSender.class) {
                if (iAcsClient == null) {
                    String aliyunAccessKeyId = (String) configMap.get("aliyunAccessKeyId");
                    String aliyunAccessKeySecret = (String) configMap.get("aliyunAccessKeySecret");

                    // 创建DefaultAcsClient实例并初始化
                    DefaultProfile profile = DefaultProfile.getProfile("cn-hangzhou", aliyunAccessKeyId, aliyunAccessKeySecret);

                    // 多个SDK client共享一个连接池，此处设置该连接池的参数，
                    // 比如每个host的最大连接数，超时时间等
                    HttpClientConfig clientConfig = HttpClientConfig.getDefault();
                    clientConfig.setMaxRequestsPerHost(10);
                    clientConfig.setConnectionTimeoutMillis(10000L);

                    profile.setHttpClientConfig(clientConfig);
                    iAcsClient = new DefaultAcsClient(profile);
                }
            }
        }
        return iAcsClient;
    }
}
