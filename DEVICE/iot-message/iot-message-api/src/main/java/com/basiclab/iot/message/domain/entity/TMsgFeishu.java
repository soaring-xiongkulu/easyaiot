package com.basiclab.iot.message.domain.entity;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;

/**
 * 飞书消息实体
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
public class TMsgFeishu implements Serializable {
    private String id;

    private Integer msgType;

    private String msgName;

    private String radioType;

    private String feishuMsgType;

    private String webHook;

    private String content;

    private Date createTime;

    private Date modifiedTime;

    private String previewUser;

    private String title;

    private String imgUrl;

    private String btnTxt;

    private String btnUrl;

    private String url;

    private String userGroupId;

    private String userGroupName;

    private static final long serialVersionUID = 1L;

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Integer getMsgType() {
        return msgType;
    }

    public void setMsgType(Integer msgType) {
        this.msgType = msgType;
    }

    public String getMsgName() {
        return msgName;
    }

    public void setMsgName(String msgName) {
        this.msgName = msgName == null ? null : msgName.trim();
    }

    public String getRadioType() {
        return radioType;
    }

    public void setRadioType(String radioType) {
        this.radioType = radioType == null ? null : radioType.trim();
    }

    public String getFeishuMsgType() {
        return feishuMsgType;
    }

    public void setFeishuMsgType(String feishuMsgType) {
        this.feishuMsgType = feishuMsgType == null ? null : feishuMsgType.trim();
    }

    public String getWebHook() {
        return webHook;
    }

    public void setWebHook(String webHook) {
        this.webHook = webHook == null ? null : webHook.trim();
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content == null ? null : content.trim();
    }

    public String getPreviewUser() {
        return previewUser;
    }

    public void setPreviewUser(String previewUser) {
        this.previewUser = previewUser == null ? null : previewUser.trim();
    }
}

