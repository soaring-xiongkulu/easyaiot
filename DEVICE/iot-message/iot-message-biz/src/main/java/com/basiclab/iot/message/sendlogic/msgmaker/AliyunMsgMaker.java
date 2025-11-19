package com.basiclab.iot.message.sendlogic.msgmaker;

import cn.hutool.json.JSONUtil;
import com.aliyuncs.dysmsapi.model.v20170525.SendSmsRequest;
import com.aliyuncs.http.MethodType;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.entity.TMsgSms;
import com.basiclab.iot.message.domain.entity.TTemplateData;
import com.basiclab.iot.message.domain.model.bean.TemplateData;
import com.basiclab.iot.message.mapper.TPreviewUserGroupMapper;
import com.basiclab.iot.message.mapper.TPreviewUserMapper;
import com.basiclab.iot.message.service.MessageConfigService;
import com.basiclab.iot.message.service.MessagePrepareService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.swing.table.DefaultTableModel;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 阿里云短信-消息加工器
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Slf4j
@Component
public class AliyunMsgMaker extends BaseMsgMaker implements IMsgMaker {

    public static String templateId;

    public static List<TemplateData> templateDataList;

    @Autowired
    private MessagePrepareService messagePrepareService;

    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private TPreviewUserMapper tPreviewUserMapper;

    @Autowired
    private TPreviewUserGroupMapper tPreviewUserGroupMapper;

    /**
     * 准备(界面字段等)
     */
    @Override
    public void prepare() {
        templateId = "";

//        if (AliYunMsgForm.getInstance().getTemplateMsgDataTable().getModel().getRowCount() == 0) {
//            AliYunMsgForm.initTemplateDataTable();
//        }

//        DefaultTableModel tableModel = (DefaultTableModel) AliYunMsgForm.getInstance().getTemplateMsgDataTable().getModel();
        DefaultTableModel tableModel = new DefaultTableModel();
        int rowCount = tableModel.getRowCount();
        TemplateData templateData;
        templateDataList = Lists.newArrayList();
        for (int i = 0; i < rowCount; i++) {
            String name = ((String) tableModel.getValueAt(i, 0)).trim();
            String value = ((String) tableModel.getValueAt(i, 1)).trim();
            templateData = new TemplateData();
            templateData.setName(name);
            templateData.setValue(value);
            templateDataList.add(templateData);
        }

    }

    /**
     * 组织阿里云短信消息
     *
     * @param msgId 消息信息
     * @return SendSmsRequest
     */
    @Override
    public SendSmsRequest makeMsg(String msgId) {
        SendSmsRequest request = new SendSmsRequest();
        //使用post提交
        request.setSysMethod(MethodType.POST);
        //必填:短信签名-可在短信控制台中找到

        TMsgSms tMsgSms = messagePrepareService.querySmsByMsgId(msgId);
        MessageConfig messageConfig = messageConfigService.queryByMsgType(1);
        Map<String,Object> configMap = messageConfig.getConfigurationMap();
        request.setSignName((String) configMap.get("aliyunSign"));
        String phoneNumbers = "";
        String userGroupId = tMsgSms.getUserGroupId();
        if(StringUtils.isNotEmpty(userGroupId)){
            String previewUserId = tPreviewUserGroupMapper.queryPreviewUserIds(userGroupId);
            List<String> previewUserIds = Arrays.asList(previewUserId.split(","));
            List<String> previewUsers = tPreviewUserMapper.queryPreviewUsers(previewUserIds);
            if(CollectionUtils.isNotEmpty(previewUsers)){
                StringBuffer sb = new StringBuffer();
                for(String previewUser : previewUsers){
                    sb.append(previewUser).append(",");
                }
                phoneNumbers = sb.substring(0,sb.lastIndexOf(",")).toString();
            }
        }
//        request.setPhoneNumbers(tMsgSms.getPreviewUser());
        log.info("aliyun sms msg phoneNumbers is:"+phoneNumbers);
        request.setPhoneNumbers(phoneNumbers);
        List<TTemplateData> templateDataList = tMsgSms.getTemplateDataList();
        // 模板参数
        Map<String, String> paramMap = new HashMap<>(10);

        for (TTemplateData templateData : templateDataList) {
            paramMap.put(templateData.getName(),templateData.getValue());
        }

        request.setTemplateParam(JSONUtil.parseFromMap(paramMap).toJSONString(0));

        // 短信模板ID，传入的模板必须是在阿里阿里云短信中的可用模板。示例：SMS_585014
        request.setTemplateCode(tMsgSms.getTemplateId());

        return request;
    }
}
