package com.basiclab.iot.message.domain.entity;

import lombok.Data;

import java.io.Serializable;
import java.util.Date;
import java.util.List;

@Data
public class TMsgSms implements Serializable {
    private String id;

    private Integer msgType;

    private String msgName;

    private String templateId;

    private String content;

    private Date createTime;

    private Date modifiedTime;

    private String previewUser;

    private List<TTemplateData> templateDataList;

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

    public String getTemplateId() {
        return templateId;
    }

    public void setTemplateId(String templateId) {
        this.templateId = templateId == null ? null : templateId.trim();
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
    public List<TTemplateData> getTemplateDataList() {
        return templateDataList;
    }

    public void setTemplateDataList(List<TTemplateData> templateDataList) {
        this.templateDataList = templateDataList;
    }
}