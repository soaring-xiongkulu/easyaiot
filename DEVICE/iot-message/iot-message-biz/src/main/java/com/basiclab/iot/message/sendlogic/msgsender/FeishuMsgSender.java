package com.basiclab.iot.message.sendlogic.msgsender;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.message.domain.entity.TMsgFeishu;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.mapper.TMsgFeishuMapper;
import com.basiclab.iot.message.sendlogic.msgmaker.FeishuMsgMaker;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

/**
 * 飞书消息发送器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-12-04
 */
@Slf4j
@Component
public class FeishuMsgSender implements IMsgSender {

    @Autowired
    private FeishuMsgMaker feishuMsgMaker;

    @Autowired
    private TMsgFeishuMapper tMsgFeishuMapper;

    @Override
    public SendResult send(String msgId) {
        log.info("飞书发送开始 params is:" + msgId);
        SendResult sendResult = new SendResult();
        
        try {
            TMsgFeishu feishuMsg = feishuMsgMaker.makeMsg(msgId);
            if (feishuMsg == null) {
                sendResult.setSuccess(false);
                sendResult.setInfo("飞书消息不存在: " + msgId);
                return sendResult;
            }
            
            sendResult.setMsgName(feishuMsg.getMsgName());
            
            String webHook = feishuMsg.getWebHook();
            if (StringUtils.isEmpty(webHook)) {
                sendResult.setSuccess(false);
                sendResult.setInfo("飞书Webhook地址不能为空");
                return sendResult;
            }
            
            // 构建飞书消息体
            JSONObject messageBody = buildFeishuMessage(feishuMsg);
            
            // 发送HTTP请求到飞书Webhook
            HttpResponse response = HttpRequest.post(webHook)
                    .header("Content-Type", "application/json")
                    .body(messageBody.toJSONString())
                    .timeout(10000)
                    .execute();
            
            String responseBody = response.body();
            log.info("飞书消息发送响应: {}", responseBody);
            
            // 解析响应
            if (response.isOk()) {
                JSONObject responseJson = JSONObject.parseObject(responseBody);
                Integer code = responseJson.getInteger("code");
                if (code != null && code == 0) {
                    sendResult.setSuccess(true);
                    sendResult.setInfo("发送成功");
                } else {
                    sendResult.setSuccess(false);
                    sendResult.setInfo(responseJson.getString("msg") != null ? 
                            responseJson.getString("msg") : responseBody);
                }
            } else {
                sendResult.setSuccess(false);
                sendResult.setInfo("HTTP请求失败: " + response.getStatus() + ", " + responseBody);
            }
            
        } catch (Exception e) {
            sendResult.setSuccess(false);
            sendResult.setInfo(e.getMessage());
            log.error("飞书消息发送失败: {}", ExceptionUtils.getStackTrace(e));
            return sendResult;
        }
        
        return sendResult;
    }

    /**
     * 构建飞书消息体
     * 飞书支持多种消息类型：text、post、image、interactive等
     */
    private JSONObject buildFeishuMessage(TMsgFeishu feishuMsg) {
        JSONObject message = new JSONObject();
        String msgType = feishuMsg.getFeishuMsgType();
        
        if (StringUtils.isEmpty(msgType) || "文本消息".equals(msgType)) {
            // 文本消息
            JSONObject textContent = new JSONObject();
            textContent.put("text", feishuMsg.getContent() != null ? feishuMsg.getContent() : "");
            message.put("msg_type", "text");
            message.put("content", textContent);
        } else if ("富文本消息".equals(msgType) || "post".equals(msgType)) {
            // 富文本消息（post格式）
            JSONObject postContent = new JSONObject();
            JSONObject post = new JSONObject();
            JSONObject zhCn = new JSONObject();
            zhCn.put("title", feishuMsg.getTitle() != null ? feishuMsg.getTitle() : "");
            
            // 构建内容数组
            JSONArray contentArray = new JSONArray();
            if (StringUtils.isNotEmpty(feishuMsg.getContent())) {
                JSONArray textArray = new JSONArray();
                textArray.add("text");
                textArray.add(feishuMsg.getContent());
                contentArray.add(textArray);
            }
            zhCn.put("content", contentArray);
            
            post.put("zh_cn", zhCn);
            postContent.put("post", post);
            message.put("msg_type", "post");
            message.put("content", postContent);
        } else if ("卡片消息".equals(msgType) || "interactive".equals(msgType)) {
            // 交互式卡片消息
            JSONObject card = new JSONObject();
            card.put("config", new JSONObject());
            
            JSONObject header = new JSONObject();
            JSONObject title = new JSONObject();
            title.put("tag", "plain_text");
            title.put("content", feishuMsg.getTitle() != null ? feishuMsg.getTitle() : "告警通知");
            header.put("title", title);
            card.put("header", header);
            
            JSONArray elements = new JSONArray();
            if (StringUtils.isNotEmpty(feishuMsg.getContent())) {
                JSONObject textElement = new JSONObject();
                textElement.put("tag", "div");
                JSONObject textContent = new JSONObject();
                textContent.put("tag", "lark_md");
                textContent.put("content", feishuMsg.getContent());
                textElement.put("text", textContent);
                elements.add(textElement);
            }
            card.put("elements", elements);
            
            message.put("msg_type", "interactive");
            message.put("card", card);
        } else {
            // 默认使用文本消息
            JSONObject textContent = new JSONObject();
            textContent.put("text", feishuMsg.getContent() != null ? feishuMsg.getContent() : "");
            message.put("msg_type", "text");
            message.put("content", textContent);
        }
        
        return message;
    }

    @Override
    public SendResult asyncSend(String[] msgData) {
        return null;
    }
}

