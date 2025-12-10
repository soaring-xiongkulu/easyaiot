package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.message.domain.entity.*;
import com.basiclab.iot.message.domain.model.vo.MessagePrepareVO;
import com.basiclab.iot.message.mapper.*;
import com.basiclab.iot.message.service.MessagePrepareService;
import org.apache.commons.collections4.CollectionUtils;
import org.jetbrains.annotations.NotNull;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

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
    private TMsgFeishuMapper tMsgFeishuMapper;
    @Autowired
    private TTemplateDataMapper templateDataMapper;
    @Autowired
    private TPushHistoryMapper tPushHistoryMapper;

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
                // 如果ID已存在，使用已有ID；否则生成新ID
                if (tMsgMail.getId() == null || tMsgMail.getId().isEmpty()) {
                    tMsgMail.setId(UUID.randomUUID().toString());
                }
                tMsgMail.setCreateTime(new Date());
                tMsgMailMapper.insert(tMsgMail);
                messagePrepareVO.setT_Msg_Mail(tMsgMail);
                return messagePrepareVO;
            case 4 :
                TMsgWxCp tMsgWxCp = messagePrepareVO.getT_Msg_Wx_Cp();
                // 如果ID已存在，使用已有ID；否则生成新ID
                if (tMsgWxCp.getId() == null || tMsgWxCp.getId().isEmpty()) {
                    tMsgWxCp.setId(UUID.randomUUID().toString());
                }
                tMsgWxCp.setCreateTime(new Date());
                tMsgWxCpMapper.insert(tMsgWxCp);
                messagePrepareVO.setT_Msg_Wx_Cp(tMsgWxCp);
                return messagePrepareVO;
            case 5 :
                TMsgHttp tMsgHttp = messagePrepareVO.getT_Msg_Http();
                // 如果ID已存在，使用已有ID；否则生成新ID
                if (tMsgHttp.getId() == null || tMsgHttp.getId().isEmpty()) {
                    tMsgHttp.setId(UUID.randomUUID().toString());
                }
                tMsgHttp.setCreateTime(new Date());
                tMsgHttpMapper.insert(tMsgHttp);
                messagePrepareVO.setT_Msg_Http(tMsgHttp);
                return messagePrepareVO;
            case 6 :
                TMsgDing tMsgDing = messagePrepareVO.getT_Msg_Ding();
                // 如果ID已存在，使用已有ID；否则生成新ID
                if (tMsgDing.getId() == null || tMsgDing.getId().isEmpty()) {
                    tMsgDing.setId(UUID.randomUUID().toString());
                }
                tMsgDing.setCreateTime(new Date());
                tMsgDingMapper.insert(tMsgDing);
                messagePrepareVO.setT_Msg_Ding(tMsgDing);
                return messagePrepareVO;
            case 7 :
                TMsgFeishu tMsgFeishu = messagePrepareVO.getT_Msg_Feishu();
                // 如果ID已存在，使用已有ID；否则生成新ID
                if (tMsgFeishu.getId() == null || tMsgFeishu.getId().isEmpty()) {
                    tMsgFeishu.setId(UUID.randomUUID().toString());
                }
                tMsgFeishu.setCreateTime(new Date());
                tMsgFeishuMapper.insert(tMsgFeishu);
                messagePrepareVO.setT_Msg_Feishu(tMsgFeishu);
                return messagePrepareVO;
        }
        return messagePrepareVO;
    }

    @NotNull
    private MessagePrepareVO addSmsMessage(MessagePrepareVO messagePrepareVO,int msgType) {
        TMsgSms tMsgSms = messagePrepareVO.getT_Msg_Sms();
        List<TTemplateData> templateDataList = messagePrepareVO.getTemplateDataList();
        // 如果ID已存在，使用已有ID；否则生成新ID
        if (tMsgSms.getId() == null || tMsgSms.getId().isEmpty()) {
            tMsgSms.setId(UUID.randomUUID().toString());
        }
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
            case 7 :
                TMsgFeishu tMsgFeishu = messagePrepareVO.getT_Msg_Feishu();
                tMsgFeishu.setModifiedTime(new Date());
                tMsgFeishuMapper.updateByPrimaryKeySelective(tMsgFeishu);
                messagePrepareVO.setT_Msg_Feishu(tMsgFeishu);
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
    @Transactional(rollbackFor = Exception.class)
    public String delete(int msgType, String id) {
        // 先检查记录是否存在
        boolean recordExists = false;
        switch (msgType){
            case 1 :
            case 2 :
                recordExists = tMsgSmsMapper.selectByPrimaryKey(id) != null;
                break;
            case 3 :
                recordExists = tMsgMailMapper.selectByPrimaryKey(id) != null;
                break;
            case 4 :
                recordExists = tMsgWxCpMapper.selectByPrimaryKey(id) != null;
                break;
            case 5 :
                recordExists = tMsgHttpMapper.selectByPrimaryKey(id) != null;
                break;
            case 6 :
                recordExists = tMsgDingMapper.selectByPrimaryKey(id) != null;
                break;
            case 7 :
                recordExists = tMsgFeishuMapper.selectByPrimaryKey(id) != null;
                break;
            default: 
                return "";
        }
        
        // 如果记录不存在，直接返回（认为删除成功，因为目标状态已经达成）
        if (!recordExists) {
            return id;
        }
        
        // 先删除关联数据：模板数据和推送历史
        templateDataMapper.deleteByMsgTypeAndMsgId(msgType, id);
        tPushHistoryMapper.deleteByMsgIdAndMsgType(id, msgType);
        
        // 再删除主表数据
        int result = 0;
        switch (msgType){
            case 1 :
                result = tMsgSmsMapper.deleteByPrimaryKey(id);
                break;
            case 2 :
                result = tMsgSmsMapper.deleteByPrimaryKey(id);
                break;
            case 3 :
                result = tMsgMailMapper.deleteByPrimaryKey(id);
                break;
            case 4 :
                result = tMsgWxCpMapper.deleteByPrimaryKey(id);
                break;
            case 5 :
                result = tMsgHttpMapper.deleteByPrimaryKey(id);
                break;
            case 6 :
                result = tMsgDingMapper.deleteByPrimaryKey(id);
                break;
            case 7 :
                result = tMsgFeishuMapper.deleteByPrimaryKey(id);
                break;
            default: 
                return "";
        }
        
        // 检查删除结果（如果记录存在但删除失败，抛出异常）
        if (result <= 0) {
            throw new RuntimeException("删除失败，未找到要删除的记录，msgType=" + msgType + ", id=" + id);
        }
        
        return id;
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
            case 7:
                List<TMsgFeishu> tMsgFeishus = tMsgFeishuMapper.selectByMsgTypeAndMsgName(msgType,msgName);
                for(TMsgFeishu tMsgFeishu : CollectionUtils.emptyIfNull(tMsgFeishus)){
                    String userGroupName = tPreviewUserGroupMapper.getGroupNameById(tMsgFeishu.getUserGroupId());
                    tMsgFeishu.setUserGroupName(userGroupName);
                }
                return tMsgFeishus;
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
