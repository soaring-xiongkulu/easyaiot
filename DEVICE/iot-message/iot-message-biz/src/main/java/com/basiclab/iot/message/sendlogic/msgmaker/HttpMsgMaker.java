package com.basiclab.iot.message.sendlogic.msgmaker;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONObject;
import com.google.common.collect.Lists;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgHttp;
import com.basiclab.iot.message.domain.model.bean.HttpMsg;
import com.basiclab.iot.message.mapper.MessageConfigMapper;
import com.basiclab.iot.message.mapper.TMsgHttpMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.time.DateUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.swing.table.DefaultTableModel;
import java.net.HttpCookie;
import java.text.ParseException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * http消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Slf4j
@Component
public class HttpMsgMaker extends BaseMsgMaker implements IMsgMaker {

    public static String method;
    public static String url;
    public static String body;
    public static String bodyType;
    public static JSONArray paramList;
    public static JSONArray headerList;
    public static JSONArray cookieList;

    @Autowired
    private TMsgHttpMapper tMsgHttpMapper;

    @Autowired
    private MessageConfigMapper messageConfigMapper;

    @Override
    public void prepare() {
        method = "";
        url = "";
        body = "";
        bodyType = "";

        // Params=========================
//        if (HttpMsgForm.getInstance().getParamTable().getModel().getRowCount() == 0) {
//            HttpMsgForm.initParamTable();
//        }
        DefaultTableModel paramTableModel = new DefaultTableModel();
        int rowCount = paramTableModel.getRowCount();

        for (int i = 0; i < rowCount; i++) {
            String name = ((String) paramTableModel.getValueAt(i, 0)).trim();
            String value = ((String) paramTableModel.getValueAt(i, 1)).trim();
            JSONObject jsonObject = new JSONObject();
            jsonObject.put("name",name);
            jsonObject.put("value",value);
            paramList.add(jsonObject);
        }
        // Headers=========================
//        if (HttpMsgForm.getInstance().getHeaderTable().getModel().getRowCount() == 0) {
//            HttpMsgForm.initHeaderTable();
//        }
//        DefaultTableModel headerTableModel = (DefaultTableModel) HttpMsgForm.getInstance().getHeaderTable().getModel();
//        rowCount = headerTableModel.getRowCount();
//        headerList = Lists.newArrayList();
//        for (int i = 0; i < rowCount; i++) {
//            String name = ((String) headerTableModel.getValueAt(i, 0)).trim();
//            String value = ((String) headerTableModel.getValueAt(i, 1)).trim();
//            nameValueObject = new HttpMsgForm.NameValueObject();
//            nameValueObject.setName(name);
//            nameValueObject.setValue(value);
//            headerList.add(nameValueObject);
//        }
//        // Cookies=========================
//        if (HttpMsgForm.getInstance().getCookieTable().getModel().getRowCount() == 0) {
//            HttpMsgForm.initCookieTable();
//        }
//        DefaultTableModel cookieTableModel = (DefaultTableModel) HttpMsgForm.getInstance().getCookieTable().getModel();
//        rowCount = cookieTableModel.getRowCount();
//        cookieList = Lists.newArrayList();
//        HttpMsgForm.CookieObject cookieObject;
//        for (int i = 0; i < rowCount; i++) {
//            String name = ((String) cookieTableModel.getValueAt(i, 0)).trim();
//            String value = ((String) cookieTableModel.getValueAt(i, 1)).trim();
//            String domain = ((String) cookieTableModel.getValueAt(i, 2)).trim();
//            String path = ((String) cookieTableModel.getValueAt(i, 3)).trim();
//            String expiry = ((String) cookieTableModel.getValueAt(i, 4)).trim();
//            cookieObject = new HttpMsgForm.CookieObject();
//            cookieObject.setName(name);
//            cookieObject.setValue(value);
//            cookieObject.setDomain(domain);
//            cookieObject.setPath(path);
//            cookieObject.setExpiry(expiry);
//            cookieList.add(cookieObject);
//        }
    }

    @Override
    public HttpMsg makeMsg(String msgId) {
        log.info("开始构建HttpMsg, msgId: {}", msgId);
        HttpMsg httpMsg = new HttpMsg();
        try {
            log.debug("查询MessageConfig, msgId: {}, msgType: 5", msgId);
            MessageConfig messageConfig = messageConfigMapper.selectByMsgType(5);
            if (messageConfig == null) {
                log.error("MessageConfig未找到, msgId: {}, msgType: 5", msgId);
                throw new RuntimeException("MessageConfig未找到, msgType: 5");
            }
            log.debug("MessageConfig查询成功, msgId: {}", msgId);
            
            Map<String,Object> configMap = JSONObject.parseObject(messageConfig.getConfiguration());
            log.debug("Configuration解析成功, msgId: {}, configKeys: {}", msgId, configMap.keySet());
            
            log.debug("查询TMsgHttp, msgId: {}", msgId);
            TMsgHttp tMsgHttp = tMsgHttpMapper.selectByPrimaryKey(msgId);
            if (tMsgHttp == null) {
                log.error("TMsgHttp未找到, msgId: {}", msgId);
                throw new RuntimeException("TMsgHttp未找到, msgId: " + msgId);
            }
            log.info("TMsgHttp查询成功, msgId: {}, msgName: {}, url: {}, method: {}", 
                    msgId, tMsgHttp.getMsgName(), tMsgHttp.getUrl(), tMsgHttp.getMethod());

            httpMsg.setUrl(tMsgHttp.getUrl());
            httpMsg.setBody(tMsgHttp.getBody());
            httpMsg.setMethod(tMsgHttp.getMethod());
            httpMsg.setBodyType(tMsgHttp.getBodyType());
            httpMsg.setHttpUseProxy((Boolean) configMap.get("isHttpUseProxy"));
            
            // 详细记录从数据库读取的值
            String bodyValue = tMsgHttp.getBody();
            String bodyTypeValue = tMsgHttp.getBodyType();
            String paramsValue = tMsgHttp.getParams();
            log.info("从数据库读取的值 - msgId: {}, body: [{}], bodyType: [{}], params: [{}]", 
                    msgId, 
                    bodyValue != null ? bodyValue : "null",
                    bodyTypeValue != null ? bodyTypeValue : "null",
                    paramsValue != null ? paramsValue : "null");
            
            log.info("HttpMsg基本属性设置完成, msgId: {}, url: {}, method: {}, bodyType: {}, body: {}, bodyLength: {}, useProxy: {}", 
                    msgId, tMsgHttp.getUrl(), tMsgHttp.getMethod(), tMsgHttp.getBodyType(), 
                    bodyValue != null ? bodyValue : "null",
                    bodyValue != null ? bodyValue.length() : 0,
                    configMap.get("isHttpUseProxy"));

            log.debug("解析参数, msgId: {}, params: {}", msgId, paramsValue);
            Map<String,Object> paramMap = parseToMap(paramsValue);
            httpMsg.setParamMap(paramMap);
            log.info("参数解析完成, msgId: {}, paramCount: {}, paramMap: {}", msgId, paramMap.size(), paramMap);
            
            // 如果body有值，清空paramMap，避免冲突
            if (bodyValue != null && !bodyValue.trim().isEmpty()) {
                log.info("检测到body有值，清空paramMap以避免冲突, msgId: {}, bodyLength: {}", msgId, bodyValue.length());
                httpMsg.setParamMap(new HashMap<>());
            } else {
                log.warn("body为空或null，将使用params, msgId: {}, paramCount: {}", msgId, paramMap.size());
            }

            log.debug("解析请求头, msgId: {}, headers: {}", msgId, tMsgHttp.getHeaders());
            Map<String,Object> headerMap = parseToMap(tMsgHttp.getHeaders());
            httpMsg.setHeaderMap(headerMap);
            log.debug("请求头解析完成, msgId: {}, headerCount: {}", msgId, headerMap.size());

        List<HttpCookie> cookies = Lists.newArrayList();
        if (tMsgHttp.getCookies() != null && !tMsgHttp.getCookies().trim().isEmpty()) {
            try {
                JSONArray jsonArray = JSONArray.parseArray(tMsgHttp.getCookies());
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
                                try {
                                    String expiry = jsonObject.getString("expiry");
                                    if (expiry != null && !expiry.trim().isEmpty()) {
                                        httpCookie.setMaxAge(DateUtils.parseDate(expiry, "yyyy-MM-dd HH:mm:ss").getTime());
                                    }
                                } catch (ParseException e) {
                                    log.error("解析cookie过期时间失败: {}", e.getMessage());
                                }
                                cookies.add(httpCookie);
                            }
                        }
                    }
                }
            } catch (Exception e) {
                log.error("解析cookies失败: {}, 错误: {}", tMsgHttp.getCookies(), e.getMessage());
            }
        }
            httpMsg.setCookies(cookies);
            httpMsg.setMsgName(tMsgHttp.getMsgName());
            log.info("HttpMsg构建完成, msgId: {}, msgName: {}, url: {}, method: {}, paramCount: {}, headerCount: {}, cookieCount: {}", 
                    msgId, tMsgHttp.getMsgName(), tMsgHttp.getUrl(), tMsgHttp.getMethod(), 
                    paramMap.size(), headerMap.size(), cookies.size());

            return httpMsg;
        } catch (Exception e) {
            log.error("构建HttpMsg失败, msgId: {}, error: {}", msgId, e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 将JSON字符串解析为Map，支持JSON对象和JSON数组两种格式
     * 如果是JSON数组格式 [{"name":"key","value":"value"}]，会转换为 {"key":"value"}
     * 如果是JSON对象格式 {"key":"value"}，直接解析
     * 如果是空字符串、null或空数组，返回空Map
     *
     * @param jsonStr JSON字符串
     * @return Map对象
     */
    private Map<String, Object> parseToMap(String jsonStr) {
        if (jsonStr == null || jsonStr.trim().isEmpty()) {
            return new HashMap<>();
        }
        
        String trimmed = jsonStr.trim();
        
        // 如果是空数组，返回空Map
        if ("[]".equals(trimmed)) {
            return new HashMap<>();
        }
        
        try {
            // 尝试解析为JSON数组格式 [{"name":"key","value":"value"}]
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
            
            // 尝试解析为JSON对象格式 {"key":"value"}
            if (trimmed.startsWith("{")) {
                JSONObject jsonObject = JSONObject.parseObject(trimmed);
                if (jsonObject != null) {
                    Map<String, Object> resultMap = new HashMap<>();
                    for (String key : jsonObject.keySet()) {
                        resultMap.put(key, jsonObject.get(key));
                    }
                    return resultMap;
                }
            }
        } catch (Exception e) {
            log.error("解析JSON字符串失败: {}, 错误: {}", jsonStr, e.getMessage());
        }
        
        // 如果解析失败，返回空Map
        return new HashMap<>();
    }
}
