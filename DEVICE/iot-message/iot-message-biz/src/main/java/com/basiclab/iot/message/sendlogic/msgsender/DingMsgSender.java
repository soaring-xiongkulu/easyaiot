package com.basiclab.iot.message.sendlogic.msgsender;

import cn.hutool.cache.CacheUtil;
import cn.hutool.cache.impl.TimedCache;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.dingtalk.api.DefaultDingTalkClient;
import com.dingtalk.api.DingTalkClient;
import com.dingtalk.api.request.OapiGettokenRequest;
import com.dingtalk.api.request.OapiMessageCorpconversationAsyncsendV2Request;
import com.dingtalk.api.request.OapiRobotSendRequest;
import com.dingtalk.api.response.OapiGettokenResponse;
import com.dingtalk.api.response.OapiMessageCorpconversationAsyncsendV2Response;
import com.dingtalk.api.response.OapiRobotSendResponse;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgDing;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TMsgDingMapper;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.sendlogic.PushControl;
import com.basiclab.iot.message.sendlogic.msgmaker.DingMsgMaker;
import com.basiclab.iot.message.service.MessageConfigService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.apache.kafka.common.errors.ApiException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

/**
 * 钉钉消息发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Slf4j
@Component
public class DingMsgSender implements IMsgSender {
    public volatile static DefaultDingTalkClient robotClient;
    public static TimedCache<String, String> accessTokenTimedCache;

    @Autowired
    private DingMsgMaker dingMsgMaker;

    @Autowired
    private TMsgDingMapper tMsgDingMapper;

    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;

    @Override
    public SendResult send(String msgId) {
        log.info("钉钉发送开始 params is:"+msgId);
        TMsgDing tMsgDing = tMsgDingMapper.selectByPrimaryKey(msgId);
        if ("work".equals(tMsgDing.getRadioType())) {
            return sendWorkMsg(msgId);
        } else {
            return sendRobotMsg(msgId);
        }
    }

    public SendResult sendWorkMsg(String msgId) {
        DefaultDingTalkClient defaultDingTalkClient = getDefaultDingTalkClient();
        SendResult sendResult = new SendResult();

        try {
            TMsgDing dingMsg = dingMsgMaker.makeMsg(msgId);
            sendResult.setMsgName(dingMsg.getMsgName());


//            String userId = dingMsg.getPreviewUser();
            List<String> previewUsers = new ArrayList<>();
            String userGroupId = dingMsg.getUserGroupId();
            if(StringUtils.isNotEmpty(userGroupId)){
                String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
                List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
                previewUsers  = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
            }
            OapiMessageCorpconversationAsyncsendV2Request request2 = new OapiMessageCorpconversationAsyncsendV2Request();
            OapiMessageCorpconversationAsyncsendV2Response response2 = new OapiMessageCorpconversationAsyncsendV2Response();
            for(String userId : CollectionUtils.emptyIfNull(previewUsers)) {
                request2.setUseridList(userId);
                request2.setAgentId(Long.valueOf(dingMsg.getAgentId()));
                request2.setToAllUser(false);
                OapiMessageCorpconversationAsyncsendV2Request.Msg msg = getMsg(dingMsg);
                request2.setMsg(msg);

                response2 = defaultDingTalkClient.execute(request2, getAccessTokenTimedCache().get("accessToken"));
            }

            if (response2.getErrcode() != 0) {
                sendResult.setSuccess(false);
                sendResult.setInfo(response2.getErrmsg());
                log.error(response2.getErrmsg());
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

    public SendResult sendRobotMsg(String msgId) {
        SendResult sendResult = new SendResult();

        try {
            TMsgDing dingMsg = dingMsgMaker.makeMsg(msgId);
            DingTalkClient client = getRobotClient(dingMsg);
            OapiRobotSendRequest request2 = new OapiRobotSendRequest();

            sendResult.setMsgName(dingMsg.getMsgName());
            if ("文本消息".equals(dingMsg.getDingMsgType())) {
                request2.setMsgtype("text");
                OapiRobotSendRequest.Text text = new OapiRobotSendRequest.Text();
                text.setContent(dingMsg.getContent());
                request2.setText(text);
                OapiRobotSendRequest.At at = new OapiRobotSendRequest.At();
                if (dingMsg != null) {
                    List<String> mobiles = Lists.newArrayList();
                    mobiles.add(dingMsg.getPreviewUser());
                    at.setAtMobiles(mobiles);
                } else {
                    at.setIsAtAll(true);
                }
                request2.setAt(at);
            } else if ("链接消息".equals(dingMsg.getDingMsgType())) {
                request2.setMsgtype("link");
                OapiRobotSendRequest.Link link = new OapiRobotSendRequest.Link();
                link.setMessageUrl(dingMsg.getUrl());
                link.setPicUrl(dingMsg.getImgUrl());
                link.setTitle(dingMsg.getTitle());
                link.setText(dingMsg.getContent());
                request2.setLink(link);
            } else if ("markdown消息".equals(dingMsg.getDingMsgType())) {
                request2.setMsgtype("markdown");
                OapiRobotSendRequest.Markdown markdown = new OapiRobotSendRequest.Markdown();
                markdown.setTitle(dingMsg.getTitle());
                markdown.setText(dingMsg.getContent());
                request2.setMarkdown(markdown);
            } else if ("卡片消息".equals(dingMsg.getDingMsgType())) {
                request2.setMsgtype("actionCard");
                OapiRobotSendRequest.Actioncard actionCard = new OapiRobotSendRequest.Actioncard();
                actionCard.setTitle(dingMsg.getTitle());
                actionCard.setText(dingMsg.getContent());
                actionCard.setSingleTitle(dingMsg.getBtnTxt());
                actionCard.setSingleURL(dingMsg.getBtnUrl());
                request2.setActionCard(actionCard);
            }


            OapiRobotSendResponse response2 = client.execute(request2);
            if (response2.getErrcode() != 0) {
                sendResult.setSuccess(false);
                sendResult.setInfo(response2.getErrmsg());
                log.error(response2.getErrmsg());
                return sendResult;
            }

        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error(e.toString());
            return sendResult;
        }

        sendResult.setSuccess(true);
        return sendResult;
    }

    private OapiMessageCorpconversationAsyncsendV2Request.Msg getMsg(TMsgDing dingMsg) {
        OapiMessageCorpconversationAsyncsendV2Request.Msg msg = new OapiMessageCorpconversationAsyncsendV2Request.Msg();
        if ("文本消息".equals(dingMsg.getDingMsgType())) {
            msg.setMsgtype("text");
            msg.setText(new OapiMessageCorpconversationAsyncsendV2Request.Text());
            msg.getText().setContent(dingMsg.getContent());
        } else if ("链接消息".equals(dingMsg.getDingMsgType())) {
            msg.setMsgtype("link");
            msg.setLink(new OapiMessageCorpconversationAsyncsendV2Request.Link());
            msg.getLink().setTitle(dingMsg.getTitle());
            msg.getLink().setText(dingMsg.getContent());
            msg.getLink().setMessageUrl(dingMsg.getUrl());
            msg.getLink().setPicUrl(dingMsg.getImgUrl());
        } else if ("markdown消息".equals(dingMsg.getDingMsgType())) {
            msg.setMsgtype("markdown");
            msg.setMarkdown(new OapiMessageCorpconversationAsyncsendV2Request.Markdown());
            msg.getMarkdown().setText(dingMsg.getContent());
            msg.getMarkdown().setTitle(dingMsg.getTitle());
        } else if ("卡片消息".equals(dingMsg.getDingMsgType())) {
            msg.setMsgtype("action_card");
            msg.setActionCard(new OapiMessageCorpconversationAsyncsendV2Request.ActionCard());
            msg.getActionCard().setTitle(dingMsg.getTitle());
            msg.getActionCard().setMarkdown(dingMsg.getContent());
            msg.getActionCard().setSingleTitle(dingMsg.getBtnTxt());
            msg.getActionCard().setSingleUrl(dingMsg.getBtnUrl());
        }
        return msg;
    }

    @Override
    public SendResult asyncSend(String[] msgData) {
        return null;
    }

    public static DefaultDingTalkClient getDefaultDingTalkClient() {
        DefaultDingTalkClient defaultDingTalkClient = null;
        if (defaultDingTalkClient == null) {
            synchronized (PushControl.class) {
                if (defaultDingTalkClient == null) {
                    defaultDingTalkClient = new DefaultDingTalkClient("https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2");
                }
            }
        }
        return defaultDingTalkClient;
    }

    public DefaultDingTalkClient getRobotClient(TMsgDing tMsgDing) {
        if (robotClient == null) {
            synchronized (PushControl.class) {
                if (robotClient == null) {
                    robotClient = new DefaultDingTalkClient(tMsgDing.getWebHook());
                }
            }
        }
        return robotClient;
    }

    public TimedCache<String, String> getAccessTokenTimedCache() {
        MessageConfig messageConfig = messageConfigService.queryByMsgType(6);
        Map<String,Object> configMap = messageConfig.getConfigurationMap();
        if (accessTokenTimedCache == null || StringUtils.isEmpty(accessTokenTimedCache.get("accessToken"))) {
            synchronized (PushControl.class) {
                if (accessTokenTimedCache == null || StringUtils.isEmpty(accessTokenTimedCache.get("accessToken"))) {
                    DefaultDingTalkClient client = new DefaultDingTalkClient("https://oapi.dingtalk.com/gettoken");
                    OapiGettokenRequest request = new OapiGettokenRequest();
                    JSONArray jsonArray = (JSONArray) configMap.get("dingdingApp");
                    JSONObject jsonObject = jsonArray.getJSONObject(0); //以第一个应用为准
                    String agentId = (String) jsonObject.get("agentId");
                    request.setAppkey((String) jsonObject.get("appKey"));
                    request.setAppsecret((String) jsonObject.get("appSecret"));
                    request.setHttpMethod("GET");
                    OapiGettokenResponse response = null;
                    try {
                        response = client.execute(request);
                    } catch (ApiException e) {
                        e.printStackTrace();
                    } catch (com.taobao.api.ApiException e) {
                        throw new RuntimeException(e);
                    }
                    accessTokenTimedCache = CacheUtil.newTimedCache((response.getExpiresIn() - 60) * 1000);
                    accessTokenTimedCache.put("accessToken", response.getAccessToken());
                }
            }
        }
        return accessTokenTimedCache;
    }
}
