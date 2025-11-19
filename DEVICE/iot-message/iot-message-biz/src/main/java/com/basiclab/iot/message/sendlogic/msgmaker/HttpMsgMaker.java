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
        HttpMsg httpMsg = new HttpMsg();
        MessageConfig messageConfig = messageConfigMapper.selectByMsgType(5);
        Map<String,Object> configMap = JSONObject.parseObject(messageConfig.getConfiguration());
        TMsgHttp tMsgHttp = tMsgHttpMapper.selectByPrimaryKey(msgId);

        httpMsg.setUrl(tMsgHttp.getUrl());
        httpMsg.setBody(tMsgHttp.getBody());
        httpMsg.setMethod(tMsgHttp.getMethod());
        httpMsg.setBodyType(tMsgHttp.getBodyType());
        httpMsg.setHttpUseProxy((Boolean) configMap.get("isHttpUseProxy"));

        Map<String,Object> paramMap = JSONObject.parseObject(tMsgHttp.getParams());
        httpMsg.setParamMap(paramMap);

        Map<String,Object> headerMap = JSONObject.parseObject(tMsgHttp.getHeaders());
        httpMsg.setHeaderMap(headerMap);

        JSONArray jsonArray = JSONArray.parseArray(tMsgHttp.getCookies());
        List<HttpCookie> cookies = Lists.newArrayList();
        for (Object obj : jsonArray) {
            JSONObject jsonObject = (JSONObject)obj;
            HttpCookie httpCookie = new HttpCookie(jsonObject.getString("name"), jsonObject.getString("value"));
            httpCookie.setDomain(jsonObject.getString("domain"));
            httpCookie.setPath(jsonObject.getString("path"));
            try {
                httpCookie.setMaxAge(DateUtils.parseDate(jsonObject.getString("expiry"), "yyyy-MM-dd HH:mm:ss").getTime());
            } catch (ParseException e) {
                log.error(e.toString());
            }
            cookies.add(httpCookie);
        }
        httpMsg.setCookies(cookies);
        httpMsg.setMsgName(tMsgHttp.getMsgName());

        return httpMsg;
    }
}
