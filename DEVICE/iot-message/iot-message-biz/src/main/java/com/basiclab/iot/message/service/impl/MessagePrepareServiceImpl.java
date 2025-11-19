package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.message.domain.entity.*;
import com.basiclab.iot.message.domain.model.vo.MessagePrepareVO;
import com.basiclab.iot.message.mapper.*;
import com.basiclab.iot.message.service.MessagePrepareService;
import org.apache.commons.collections4.CollectionUtils;
import org.jetbrains.annotations.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.List;
import java.util.UUID;

/**
 * 消息准备实现层Impl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@Component
public class MessagePrepareServiceImpl implements MessagePrepareService {

    @Autowired
    private TMsgMailMapper tMsgMailMapper;
    @Autowired
    private TMsgDingMapper tMsgDingMapper;
    @Autowired
    private TMsgHttpMapper tMsgHttpMapper;
    @Autowired
    private TMsgSmsMapper tMsgSmsMapper;
    @Autowired
    private TMsgWxCpMapper tMsgWxCpMapper;
    @Autowired
    private TTemplateDataMapper templateDataMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;


    @Override
    public MessagePrepareVO add(MessagePrepareVO messagePrepareVO) {
        int msgType = messagePrepareVO.getMsgType();
        switch (msgType){
            case 1 :
                return addSmsMessage(messagePrepareVO,1);
            case 2 :
                return addSmsMessage(messagePrepareVO,2);
            case 3 :
                TMsgMail tMsgMail = messagePrepareVO.getT_Msg_Mail();
                tMsgMail.setId(UUID.randomUUID().toString());
                tMsgMail.setCreateTime(new Date());
                tMsgMailMapper.insert(tMsgMail);
                messagePrepareVO.setT_Msg_Mail(tMsgMail);
                return messagePrepareVO;
            case 4 :
                TMsgWxCp tMsgWxCp = messagePrepareVO.getT_Msg_Wx_Cp();
                tMsgWxCp.setId(UUID.randomUUID().toString());
                tMsgWxCp.setCreateTime(new Date());
                tMsgWxCpMapper.insert(tMsgWxCp);
                messagePrepareVO.setT_Msg_Wx_Cp(tMsgWxCp);
                return messagePrepareVO;
            case 5 :
                TMsgHttp tMsgHttp = messagePrepareVO.getT_Msg_Http();
                tMsgHttp.setId(UUID.randomUUID().toString());
                tMsgHttp.setCreateTime(new Date());
                tMsgHttpMapper.insert(tMsgHttp);
                messagePrepareVO.setT_Msg_Http(tMsgHttp);
                return messagePrepareVO;
            case 6 :
                TMsgDing tMsgDing = messagePrepareVO.getT_Msg_Ding();
                tMsgDing.setId(UUID.randomUUID().toString());
                tMsgDing.setCreateTime(new Date());
                tMsgDingMapper.insert(tMsgDing);
                messagePrepareVO.setT_Msg_Ding(tMsgDing);
                return messagePrepareVO;
        }
        return messagePrepareVO;
    }

    @NotNull
    private MessagePrepareVO addSmsMessage(MessagePrepareVO messagePrepareVO,int msgType) {
        TMsgSms tMsgSms = messagePrepareVO.getT_Msg_Sms();
        List<TTemplateData> templateDataList = messagePrepareVO.getTemplateDataList();
        tMsgSms.setId(UUID.randomUUID().toString());
        tMsgSms.setCreateTime(new Date());
        tMsgSmsMapper.insert(tMsgSms);
        messagePrepareVO.setT_Msg_Sms(tMsgSms);
        for(TTemplateData templateData : CollectionUtils.emptyIfNull(templateDataList)){
            templateData.setId(UUID.randomUUID().toString());
            templateData.setCreateTime(new Date());
            templateData.setMsgId(tMsgSms.getId());
            templateData.setMsgType(msgType);
            templateDataMapper.insert(templateData);
        }
        return messagePrepareVO;
    }

    @Override
    public MessagePrepareVO update(MessagePrepareVO messagePrepareVO) {
        int msgType = messagePrepareVO.getMsgType();
        switch (msgType){
            case 1 :
                return updateMsgSms(messagePrepareVO,msgType);
            case 2 :
                return updateMsgSms(messagePrepareVO,msgType);
            case 3 :
                TMsgMail tMsgMail = messagePrepareVO.getT_Msg_Mail();
                tMsgMail.setModifiedTime(new Date());
                tMsgMailMapper.updateByPrimaryKeySelective(tMsgMail);
                messagePrepareVO.setT_Msg_Mail(tMsgMail);
                return messagePrepareVO;
            case 4 :
                TMsgWxCp tMsgWxCp = messagePrepareVO.getT_Msg_Wx_Cp();
                tMsgWxCp.setModifiedTime(new Date());
                tMsgWxCpMapper.updateByPrimaryKeySelective(tMsgWxCp);
                messagePrepareVO.setT_Msg_Wx_Cp(tMsgWxCp);
                return messagePrepareVO;
            case 5 :
                TMsgHttp tMsgHttp = messagePrepareVO.getT_Msg_Http();
                tMsgHttp.setModifiedTime(new Date());
                tMsgHttpMapper.updateByPrimaryKeySelective(tMsgHttp);
                messagePrepareVO.setT_Msg_Http(tMsgHttp);
                return messagePrepareVO;
            case 6 :
                TMsgDing tMsgDing = messagePrepareVO.getT_Msg_Ding();
                tMsgDing.setModifiedTime(new Date());
                tMsgDingMapper.updateByPrimaryKeySelective(tMsgDing);
                messagePrepareVO.setT_Msg_Ding(tMsgDing);
                return messagePrepareVO;
        }
        return messagePrepareVO;
    }

    @NotNull
    private MessagePrepareVO updateMsgSms(MessagePrepareVO messagePrepareVO,int msgType) {
        TMsgSms tMsgSms = messagePrepareVO.getT_Msg_Sms();
        tMsgSms.setModifiedTime(new Date());
        tMsgSmsMapper.updateByPrimaryKeySelective(tMsgSms);
        templateDataMapper.deleteByMsgTypeAndMsgId(msgType,tMsgSms.getId());
        List<TTemplateData> templateDataList = messagePrepareVO.getTemplateDataList();
        for(TTemplateData templateData : CollectionUtils.emptyIfNull(templateDataList)){
            templateData.setModifiedTime(new Date());
            templateData.setId(UUID.randomUUID().toString());
            templateData.setCreateTime(new Date());
            templateData.setMsgId(tMsgSms.getId());
            templateData.setMsgType(msgType);
            templateDataMapper.insert(templateData);
        }
        messagePrepareVO.setT_Msg_Sms(tMsgSms);
        return messagePrepareVO;
    }

    @Override
    public String delete(int msgType, String id) {
        switch (msgType){
            case 1 :
                tMsgSmsMapper.deleteByPrimaryKey(id);
                return id;
            case 2 :
                tMsgSmsMapper.deleteByPrimaryKey(id);
                return id;
            case 3 :
                tMsgMailMapper.deleteByPrimaryKey(id);
                return id;
            case 4 :
                tMsgWxCpMapper.deleteByPrimaryKey(id);
                return id;
            case 5 :
                tMsgHttpMapper.deleteByPrimaryKey(id);
                return id;
            case 6 :
                tMsgDingMapper.deleteByPrimaryKey(id);
                return id;
            default: return new String();
        }
    }

    @Override
    public List<?> query(MessagePrepareVO messagePrepareVO) {
        int msgType = messagePrepareVO.getMsgType();
        String msgName = messagePrepareVO.getMsgName();
        switch (msgType){
            case 1:
                return queryMsgSms(msgType, msgName);
            case 2:
                return queryMsgSms(msgType, msgName);
            case 3:
                List<TMsgMail> tMsgMails = tMsgMailMapper.selectByMsgTypeAndMsgName(msgType,msgName);
                for(TMsgMail tMsgMail : CollectionUtils.emptyIfNull(tMsgMails)){
                    String userGroupName = tPreviewUserGroupMapper.getGroupNameById(tMsgMail.getUserGroupId());
                    tMsgMail.setUserGroupName(userGroupName);
                }
                return tMsgMails;
            case 4:
                List<TMsgWxCp> tMsgWxCps = tMsgWxCpMapper.selectByMsgTypeAndMsgName(msgType,msgName);
                for(TMsgWxCp tMsgWxCp : CollectionUtils.emptyIfNull(tMsgWxCps)){
                    String userGroupName = tPreviewUserGroupMapper.getGroupNameById(tMsgWxCp.getUserGroupId());
                    tMsgWxCp.setUserGroupName(userGroupName);
                }

                return tMsgWxCps;
            case 5:
                List<TMsgHttp> tMsgHttps = tMsgHttpMapper.selectByMsgTypeAndMsgName(msgType,msgName);

                return tMsgHttps;
            case 6:
                List<TMsgDing> tMsgDings = tMsgDingMapper.selectByMsgTypeAndMsgName(msgType,msgName);
                for(TMsgDing tMsgDing : CollectionUtils.emptyIfNull(tMsgDings)){
                    String userGroupName = tPreviewUserGroupMapper.getGroupNameById(tMsgDing.getUserGroupId());
                    tMsgDing.setUserGroupName(userGroupName);
                }
                return tMsgDings;
            default: return null;
        }
    }

    @Override
    public TMsgSms querySmsByMsgId(String msgId) {
        TMsgSms tMsgSms = tMsgSmsMapper.selectByPrimaryKey(msgId);
        List<TTemplateData> templateDataList = templateDataMapper.selectByMsgId(msgId);
        tMsgSms.setTemplateDataList(templateDataList);
        return tMsgSms;
    }

    @NotNull
    private List<TMsgSms> queryMsgSms(int msgType, String msgName) {
        List<TMsgSms> tMsgSmsList = tMsgSmsMapper.selectByMsgTypeAndMsgName(msgType, msgName);
        for(TMsgSms tMsgSms : CollectionUtils.emptyIfNull(tMsgSmsList)){
            String msgId = tMsgSms.getId();
            List<TTemplateData> templateDataList = templateDataMapper.selectByMsgTypeAndMsgId(msgType,msgId);
            tMsgSms.setTemplateDataList(templateDataList);
            String userGroupName = tPreviewUserGroupMapper.getGroupNameById(tMsgSms.getUserGroupId());
            tMsgSms.setUserGroupName(userGroupName);
        }
        return tMsgSmsList;
    }
}
