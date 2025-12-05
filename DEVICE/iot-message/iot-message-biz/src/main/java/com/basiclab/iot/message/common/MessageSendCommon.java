package com.basiclab.iot.message.common;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.message.domain.entity.TPushHistory;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.domain.model.dto.MessageMailSendDto;
import com.basiclab.iot.message.domain.model.bean.HttpMsg;
import com.basiclab.iot.message.sendlogic.MessageTypeEnum;
import com.basiclab.iot.message.sendlogic.msgsender.*;
import com.basiclab.iot.message.service.PushHistoryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.net.HttpCookie;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import com.google.common.collect.Lists;

/**
 * 通知发送公共类
 * 支持6种通知方式：短信(阿里云/腾讯云)、邮件、企业微信、HTTP、钉钉、飞书
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Slf4j
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

    @Autowired
    private com.basiclab.iot.message.service.MessageConfigService messageConfigService;

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
     * 使用传递的参数直接发送消息（支持HTTP/Webhook）
     * 当传递了完整的HTTP参数时，直接使用这些参数发送，而不从数据库读取
     */
    public SendResult messageSendWithParams(MessageMailSendDto dto) {
        log.info("使用传递的参数直接发送消息, msgType: {}, msgId: {}", dto.getMsgType(), dto.getMsgId());
        
        // 如果是HTTP类型，使用传递的参数直接构建HttpMsg
        if (dto.getMsgType() != null && dto.getMsgType() == MessageTypeEnum.HTTP_CODE) {
            HttpMsg httpMsg = buildHttpMsgFromDto(dto);
            SendResult sendResult = httpMsgSender.sendWithHttpMsg(httpMsg);
            addPushHistory(dto.getMsgType(), dto.getMsgId(), sendResult);
            return sendResult;
        }
        
        // 其他类型，使用原有方法
        return messageSend(dto.getMsgType(), dto.getMsgId());
    }

    /**
     * 从DTO构建HttpMsg对象
     */
    private HttpMsg buildHttpMsgFromDto(MessageMailSendDto dto) {
        log.info("从DTO构建HttpMsg, msgId: {}, method: {}, url: {}", dto.getMsgId(), dto.getMethod(), dto.getUrl());
        
        HttpMsg httpMsg = new HttpMsg();
        httpMsg.setMsgName(dto.getMsgName() != null ? dto.getMsgName() : "HTTP消息");
        httpMsg.setMethod(dto.getMethod() != null ? dto.getMethod() : "POST");
        httpMsg.setUrl(dto.getUrl());
        httpMsg.setBody(dto.getBody());
        httpMsg.setBodyType(dto.getBodyType() != null ? dto.getBodyType() : "application/json");
        
        // 解析params
        Map<String, Object> paramMap = parseJsonToMap(dto.getParams());
        httpMsg.setParamMap(paramMap);
        
        // 如果body有值，清空paramMap，避免冲突
        if (dto.getBody() != null && !dto.getBody().trim().isEmpty()) {
            log.info("检测到body有值，清空paramMap以避免冲突, msgId: {}", dto.getMsgId());
            httpMsg.setParamMap(new HashMap<>());
        }
        
        // 解析headers
        Map<String, Object> headerMap = parseJsonToMap(dto.getHeaders());
        httpMsg.setHeaderMap(headerMap);
        
        // 解析cookies
        List<HttpCookie> cookies = parseJsonToCookies(dto.getCookies());
        httpMsg.setCookies(cookies);
        
        // 设置代理配置（从配置中读取）
        try {
            com.basiclab.iot.message.domain.entity.MessageConfig messageConfig = 
                messageConfigService.queryByMsgType(5);
            if (messageConfig != null) {
                Map<String, Object> configMap = messageConfig.getConfigurationMap();
                httpMsg.setHttpUseProxy((Boolean) configMap.getOrDefault("isHttpUseProxy", false));
            }
        } catch (Exception e) {
            log.warn("读取代理配置失败: {}", e.getMessage());
            httpMsg.setHttpUseProxy(false);
        }
        
        log.info("HttpMsg构建完成, msgId: {}, method: {}, url: {}, paramCount: {}, headerCount: {}, cookieCount: {}", 
                dto.getMsgId(), httpMsg.getMethod(), httpMsg.getUrl(), 
                paramMap.size(), headerMap.size(), cookies.size());
        
        return httpMsg;
    }

    /**
     * 解析JSON字符串为Map
     * 支持格式: [{"name":"key","value":"value"}] 或 {"key":"value"}
     */
    private Map<String, Object> parseJsonToMap(String jsonStr) {
        if (jsonStr == null || jsonStr.trim().isEmpty() || "[]".equals(jsonStr.trim())) {
            return new HashMap<>();
        }
        
        try {
            String trimmed = jsonStr.trim();
            // 如果是数组格式
            if (trimmed.startsWith("[")) {
                JSONArray jsonArray = JSONArray.parseArray(trimmed);
                Map<String, Object> resultMap = new HashMap<>();
                for (Object obj : jsonArray) {
                    if (obj instanceof JSONObject) {
                        JSONObject jsonObject = (JSONObject) obj;
                        String name = jsonObject.getString("name");
                        Object value = jsonObject.get("value");
                        if (name != null) {
                            resultMap.put(name, value != null ? value.toString() : "");
                        }
                    }
                }
                return resultMap;
            }
            // 如果是对象格式
            if (trimmed.startsWith("{")) {
                JSONObject jsonObject = JSONObject.parseObject(trimmed);
                Map<String, Object> resultMap = new HashMap<>();
                if (jsonObject != null) {
                    for (String key : jsonObject.keySet()) {
                        resultMap.put(key, jsonObject.get(key));
                    }
                }
                return resultMap;
            }
        } catch (Exception e) {
            log.error("解析JSON字符串失败: {}, 错误: {}", jsonStr, e.getMessage());
        }
        
        return new HashMap<>();
    }

    /**
     * 解析JSON字符串为Cookie列表
     * 格式: [{"name":"key","value":"value","domain":"","path":"","time":""}]
     */
    private List<HttpCookie> parseJsonToCookies(String jsonStr) {
        List<HttpCookie> cookies = Lists.newArrayList();
        if (jsonStr == null || jsonStr.trim().isEmpty() || "[]".equals(jsonStr.trim())) {
            return cookies;
        }
        
        try {
            JSONArray jsonArray = JSONArray.parseArray(jsonStr);
            if (jsonArray != null) {
                for (Object obj : jsonArray) {
                    if (obj instanceof JSONObject) {
                        JSONObject jsonObject = (JSONObject) obj;
                        String name = jsonObject.getString("name");
                        String value = jsonObject.getString("value");
                        if (name != null && value != null) {
                            HttpCookie httpCookie = new HttpCookie(name, value);
                            httpCookie.setDomain(jsonObject.getString("domain"));
                            httpCookie.setPath(jsonObject.getString("path"));
                            cookies.add(httpCookie);
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.error("解析cookies失败: {}, 错误: {}", jsonStr, e.getMessage());
        }
        
        return cookies;
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
