package com.basiclab.iot.message.sendlogic.msgsender;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgWxCp;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TMsgWxCpMapper;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.sendlogic.PushControl;
import com.basiclab.iot.message.sendlogic.msgmaker.WxCpMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import me.chanjar.weixin.common.util.http.apache.DefaultApacheHttpClientBuilder;
import me.chanjar.weixin.cp.api.WxCpService;
import me.chanjar.weixin.cp.api.impl.WxCpServiceApacheHttpClientImpl;
import me.chanjar.weixin.cp.bean.message.WxCpMessage;
import me.chanjar.weixin.cp.bean.message.WxCpMessageSendResult;
import me.chanjar.weixin.cp.config.impl.WxCpDefaultConfigImpl;
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
 * 企业微信模板消息发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-19
 */
@Slf4j
@Component
public class WxCpMsgSender implements IMsgSender {
    @Autowired
    private WxCpMsgMaker wxCpMsgMaker;

    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private TMsgWxCpMapper tMsgWxCpMapper;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;

    @Override
    public SendResult send(String msgId) {
        log.info("微信发送开始 params is:"+msgId);
        SendResult sendResult = new SendResult();
        WxCpService wxCpService = getWxCpServicegetWxCpService();
        try {
            WxCpMessage wxCpMessage = wxCpMsgMaker.makeMsg(msgId);
            TMsgWxCp tMsgWxCp = tMsgWxCpMapper.selectByPrimaryKey(msgId);
            sendResult.setMsgName(tMsgWxCp.getMsgName());
//            String openId = wxCpMessage.getToUser();
            List<String> previewUsers = new ArrayList<>();
            String userGroupId = tMsgWxCp.getUserGroupId();
            if(StringUtils.isNotEmpty(userGroupId)){
                String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
                List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
                previewUsers  = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
            }
            WxCpMessageSendResult wxCpMessageSendResult = new WxCpMessageSendResult();
            for(String openId : CollectionUtils.emptyIfNull(previewUsers)) {
                wxCpMessage.setToUser(openId);
                wxCpMessageSendResult  = wxCpService.getMessageService().send(wxCpMessage);
            }
            if (wxCpMessageSendResult.getErrCode() != 0 || StringUtils.isNoneEmpty(wxCpMessageSendResult.getInvalidUser())) {
                sendResult.setSuccess(false);
                sendResult.setInfo(wxCpMessageSendResult.toString());
                log.error(wxCpMessageSendResult.toString());
                return sendResult;
            }

        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(ExceptionUtils.getStackTrace(e));
            return sendResult;
        }

        sendResult.setSuccess(true);
        return sendResult;
    }

    @Override
    public SendResult asyncSend(String[] msgData) {
        return null;
    }

    /**
     * 企业微信配置
     *
     * @return WxCpConfigStorage
     */
    private WxCpDefaultConfigImpl wxCpConfigStorage() {
        MessageConfig messageConfig = messageConfigService.queryByMsgType(4);
        Map<String, Object> configMap = messageConfig.getConfigurationMap();
        JSONArray jsonArray = (JSONArray) configMap.get("wxCpApp");
        JSONObject jsonObject = new JSONObject();
        if (jsonArray.size() > 0) {
            jsonObject = jsonArray.getJSONObject(0);
        }
        WxCpDefaultConfigImpl configStorage = new WxCpDefaultConfigImpl();
        configStorage.setCorpId((String) configMap.get("wxCpCorpId"));
        String agentId = jsonObject.getString("agentId");
        configStorage.setAgentId(Integer.valueOf(agentId));
        configStorage.setCorpSecret(jsonObject.getString("secret"));
        DefaultApacheHttpClientBuilder clientBuilder = DefaultApacheHttpClientBuilder.get();
        //从连接池获取链接的超时时间(单位ms)
        clientBuilder.setConnectionRequestTimeout(10000);
        //建立链接的超时时间(单位ms)
        clientBuilder.setConnectionTimeout(5000);
        //连接池socket超时时间(单位ms)
        clientBuilder.setSoTimeout(5000);
        //空闲链接的超时时间(单位ms)
        clientBuilder.setIdleConnTimeout(60000);
        //空闲链接的检测周期(单位ms)
        clientBuilder.setCheckWaitTime(60000);
        //每路最大连接数
        clientBuilder.setMaxConnPerHost(100);
        //连接池最大连接数
        clientBuilder.setMaxTotalConn(100);
        //HttpClient请求时使用的User Agent
//        clientBuilder.setUserAgent(..)
        configStorage.setApacheHttpClientBuilder(clientBuilder);
        return configStorage;
    }

    /**
     * 获取企业微信工具服务
     *
     * @return WxCpService
     */
    public WxCpService getWxCpServicegetWxCpService() {
        WxCpService wxCpService = null;
        WxCpDefaultConfigImpl wxCpConfigStorage = null;
        if (wxCpConfigStorage == null) {
            synchronized (WxCpMsgSender.class) {
                if (wxCpConfigStorage == null) {
                    wxCpConfigStorage = wxCpConfigStorage();
                }
            }
        }
        if (wxCpService == null && wxCpConfigStorage != null) {
            synchronized (PushControl.class) {
                if (wxCpService == null && wxCpConfigStorage != null) {
                    wxCpService = new WxCpServiceApacheHttpClientImpl();
                    wxCpService.setWxCpConfigStorage(wxCpConfigStorage);
                }
            }
        }
        return wxCpService;
    }
}
