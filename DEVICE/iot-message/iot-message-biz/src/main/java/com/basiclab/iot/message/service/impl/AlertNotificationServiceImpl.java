package com.basiclab.iot.message.service.impl;

import com.basiclab.iot.message.common.MessageSendCommon;
import com.basiclab.iot.message.domain.entity.*;
import com.basiclab.iot.message.domain.model.AlertNotificationMessage;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.domain.model.vo.MessagePrepareVO;
import com.basiclab.iot.message.sendlogic.MessageTypeEnum;
import com.basiclab.iot.message.service.AlertNotificationService;
import com.basiclab.iot.message.service.MessagePrepareService;
import com.basiclab.iot.system.api.notify.NotifyTemplateApi;
import com.basiclab.iot.system.api.notify.dto.NotifyTemplateRespDTO;
import com.basiclab.iot.common.domain.CommonResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 告警通知服务实现
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Slf4j
@Service
public class AlertNotificationServiceImpl implements AlertNotificationService {

    @Autowired
    private MessageSendCommon messageSendCommon;

    @Autowired
    private MessagePrepareService messagePrepareService;

    @Resource
    private NotifyTemplateApi notifyTemplateApi;

    /**
     * 通知方式到消息类型的映射表（优化：使用Map替代switch-case）
     * 支持6种通知方式：
     * 1. 短信（sms）- 阿里云/腾讯云
     * 2. 邮件（email/mail）
     * 3. 企业微信（wxcp/wechat/weixin）
     * 4. HTTP请求（http/webhook）
     * 5. 钉钉（ding/dingtalk）
     * 6. 飞书（feishu/lark）
     */
    private static final Map<String, Integer> METHOD_TO_MSG_TYPE_MAP = new HashMap<String, Integer>() {{
        // 短信（默认使用阿里云）
        put("sms", MessageTypeEnum.ALI_YUN_CODE);
        // 邮件
        put("email", MessageTypeEnum.EMAIL_CODE);
        put("mail", MessageTypeEnum.EMAIL_CODE);
        // 企业微信
        put("wxcp", MessageTypeEnum.WX_CP_CODE);
        put("wechat", MessageTypeEnum.WX_CP_CODE);
        put("weixin", MessageTypeEnum.WX_CP_CODE);
        // HTTP/webhook
        put("http", MessageTypeEnum.HTTP_CODE);
        put("webhook", MessageTypeEnum.HTTP_CODE);
        // 钉钉
        put("ding", MessageTypeEnum.DING_CODE);
        put("dingtalk", MessageTypeEnum.DING_CODE);
        // 飞书
        put("feishu", MessageTypeEnum.FEISHU_CODE);
        put("lark", MessageTypeEnum.FEISHU_CODE);
    }};

    @Override
    public void processAlertNotification(AlertNotificationMessage notificationMessage) {
        try {
            // 使用channels配置（新方式）
            List<Map<String, Object>> channels = notificationMessage.getChannels();
            List<Map<String, Object>> notifyUsers = notificationMessage.getNotifyUsers();

            // 检查channels配置
            if (channels == null || channels.isEmpty()) {
                log.warn("告警通知消息中没有通知渠道配置: alertId={}", notificationMessage.getAlertId());
                return;
            }

            if (notifyUsers == null || notifyUsers.isEmpty()) {
                log.warn("告警通知消息中没有通知人: alertId={}", notificationMessage.getAlertId());
                return;
            }

            // 构建告警参数（用于模板替换）
            Map<String, Object> templateParams = buildTemplateParams(notificationMessage);

            // 处理每个通知渠道
            for (Map<String, Object> channel : channels) {
                try {
                    String method = (String) channel.get("method");
                    Object templateIdObj = channel.get("template_id");
                    if (method == null || templateIdObj == null) {
                        log.warn("通知渠道配置不完整: method={}, template_id={}", method, templateIdObj);
                        continue;
                    }
                    
                    // 获取模板并格式化内容
                    String content = getTemplateContent(templateIdObj, templateParams);
                    String title = buildNotificationTitle(notificationMessage);
                    
                    sendNotificationByMethod(method, notifyUsers, title, content, notificationMessage);
                } catch (Exception e) {
                    log.error("发送告警通知失败: channel={}, alertId={}, error={}",
                            channel, notificationMessage.getAlertId(), e.getMessage(), e);
                }
            }

        } catch (Exception e) {
            log.error("处理告警通知失败: alertId={}, error={}",
                    notificationMessage.getAlertId(), e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 构建模板参数（用于${}占位符替换）
     */
    private Map<String, Object> buildTemplateParams(AlertNotificationMessage notificationMessage) {
        Map<String, Object> params = new HashMap<>();
        
        AlertNotificationMessage.AlertInfo alert = notificationMessage.getAlert();
        if (alert != null) {
            params.put("object", alert.getObject());
            params.put("event", alert.getEvent());
            params.put("region", alert.getRegion() != null ? alert.getRegion() : "");
            params.put("information", alert.getInformation() != null ? alert.getInformation().toString() : "");
            params.put("time", alert.getTime() != null ? alert.getTime() : "");
            params.put("image_path", alert.getImagePath() != null ? alert.getImagePath() : "");
            params.put("record_path", alert.getRecordPath() != null ? alert.getRecordPath() : "");
        }
        
        params.put("device_id", notificationMessage.getDeviceId());
        params.put("device_name", notificationMessage.getDeviceName());
        params.put("task_id", notificationMessage.getTaskId());
        params.put("task_name", notificationMessage.getTaskName());
        
        return params;
    }

    /**
     * 获取模板内容并格式化
     */
    private String getTemplateContent(Object templateIdObj, Map<String, Object> templateParams) {
        try {
            // 将template_id转换为Long
            Long templateId = null;
            if (templateIdObj instanceof Long) {
                templateId = (Long) templateIdObj;
            } else if (templateIdObj instanceof Integer) {
                templateId = ((Integer) templateIdObj).longValue();
            } else if (templateIdObj instanceof String) {
                try {
                    templateId = Long.parseLong((String) templateIdObj);
                } catch (NumberFormatException e) {
                    log.warn("模板ID格式错误: {}", templateIdObj);
                    return buildDefaultContent(templateParams);
                }
            } else {
                log.warn("模板ID类型不支持: {}", templateIdObj.getClass().getName());
                return buildDefaultContent(templateParams);
            }

            // 通过API获取模板
            CommonResult<NotifyTemplateRespDTO> result = notifyTemplateApi.getTemplate(templateId);
            if (result != null && result.getCode() == 0 && result.getData() != null) {
                NotifyTemplateRespDTO template = result.getData();
                String templateContent = template.getContent();
                
                // 使用${}格式替换占位符
                // 将模板中的${key}替换为实际值
                String formattedContent = templateContent;
                for (Map.Entry<String, Object> entry : templateParams.entrySet()) {
                    String placeholder = "${" + entry.getKey() + "}";
                    String value = entry.getValue() != null ? entry.getValue().toString() : "";
                    formattedContent = formattedContent.replace(placeholder, value);
                }
                
                return formattedContent;
            } else {
                log.warn("获取模板失败: templateId={}, result={}", templateId, result);
                return buildDefaultContent(templateParams);
            }
            
        } catch (Exception e) {
            log.error("获取模板内容失败: templateId={}, error={}", templateIdObj, e.getMessage(), e);
            return buildDefaultContent(templateParams);
        }
    }

    /**
     * 构建默认通知内容（当模板获取失败时使用）
     */
    private String buildDefaultContent(Map<String, Object> params) {
        StringBuilder content = new StringBuilder();
        content.append("【告警通知】\n");
        content.append("设备名称: ").append(params.get("device_name")).append("\n");
        content.append("设备ID: ").append(params.get("device_id")).append("\n");
        if (params.get("object") != null) {
            content.append("对象类型: ").append(params.get("object")).append("\n");
        }
        if (params.get("event") != null) {
            content.append("事件类型: ").append(params.get("event")).append("\n");
        }
        if (params.get("region") != null && !params.get("region").toString().isEmpty()) {
            content.append("区域: ").append(params.get("region")).append("\n");
        }
        if (params.get("time") != null && !params.get("time").toString().isEmpty()) {
            content.append("告警时间: ").append(params.get("time")).append("\n");
        }
        return content.toString();
    }

    /**
     * 根据通知方式发送通知
     * 支持6种通知方式：
     * 1. 短信(sms) - 阿里云/腾讯云短信
     * 2. 邮件(email/mail) - SMTP邮件
     * 3. 企业微信(wxcp/wechat/weixin) - 企业微信应用消息
     * 4. HTTP(http/webhook) - HTTP Webhook请求
     * 5. 钉钉(ding/dingtalk) - 钉钉工作通知/群机器人
     * 6. 飞书(feishu/lark) - 飞书群机器人
     *
     * @param method 通知方式
     * @param notifyUsers 通知人列表
     * @param title 通知标题
     * @param content 通知内容
     * @param notificationMessage 告警通知消息
     */
    private void sendNotificationByMethod(
            String method,
            List<Map<String, Object>> notifyUsers,
            String title,
            String content,
            AlertNotificationMessage notificationMessage) {

        // 根据通知方式映射到消息类型
        int msgType = mapMethodToMsgType(method);
        if (msgType == 0) {
            log.warn("不支持的通知方式: method={}", method);
            return;
        }

        // 为每个通知人发送通知
        for (Map<String, Object> user : notifyUsers) {
            try {
                // 生成消息ID（用于追踪）
                String msgId = UUID.randomUUID().toString();

                // 准备并发送消息
                prepareAndSendMessage(msgType, method, user, title, content, notificationMessage, msgId);

            } catch (Exception e) {
                log.error("发送通知给用户失败: method={}, user={}, error={}",
                        method, user, e.getMessage(), e);
            }
        }
    }

    /**
     * 映射通知方式到消息类型（优化：使用Map替代switch-case）
     *
     * @param method 通知方式
     * @return 消息类型代码，如果不支持则返回0
     */
    private int mapMethodToMsgType(String method) {
        if (method == null) {
            return 0;
        }
        // 默认使用阿里云短信，如果需要支持腾讯云，需要从配置中获取
        return METHOD_TO_MSG_TYPE_MAP.getOrDefault(method.toLowerCase(), 0);
    }

    /**
     * 根据消息类型准备消息（优化：使用策略模式替代switch-case）
     */
    private void prepareMessageByType(MessagePrepareVO messagePrepareVO, int msgType,
                                       Map<String, Object> user, String title, String content, String msgId) {
        if (msgType == MessageTypeEnum.EMAIL_CODE) {
            prepareEmailMessage(messagePrepareVO, user, title, content, msgId);
        } else if (msgType == MessageTypeEnum.ALI_YUN_CODE || msgType == MessageTypeEnum.TX_YUN_CODE) {
            prepareSmsMessage(messagePrepareVO, user, content, msgType, msgId);
        } else if (msgType == MessageTypeEnum.WX_CP_CODE) {
            prepareWxCpMessage(messagePrepareVO, user, title, content, msgId);
        } else if (msgType == MessageTypeEnum.HTTP_CODE) {
            prepareHttpMessage(messagePrepareVO, user, title, content, msgId);
        } else if (msgType == MessageTypeEnum.DING_CODE) {
            prepareDingMessage(messagePrepareVO, user, title, content, msgId);
        } else if (msgType == MessageTypeEnum.FEISHU_CODE) {
            prepareFeishuMessage(messagePrepareVO, user, title, content, msgId);
        } else {
            log.warn("不支持的消息类型: msgType={}", msgType);
            throw new IllegalArgumentException("不支持的消息类型: " + msgType);
        }
    }

    /**
     * 准备并发送消息
     *
     * @param msgType 消息类型
     * @param method 通知方式
     * @param user 用户信息
     * @param title 通知标题
     * @param content 通知内容
     * @param notificationMessage 告警通知消息
     * @param msgId 消息ID
     */
    private void prepareAndSendMessage(
            int msgType,
            String method,
            Map<String, Object> user,
            String title,
            String content,
            AlertNotificationMessage notificationMessage,
            String msgId) {

        try {
            MessagePrepareVO messagePrepareVO = new MessagePrepareVO();
            messagePrepareVO.setMsgType(msgType);
            messagePrepareVO.setMsgName("告警通知-" + notificationMessage.getAlertId());

            // 根据消息类型准备消息（优化：使用策略模式）
            prepareMessageByType(messagePrepareVO, msgType, user, title, content, msgId);

            // 准备消息（保存到数据库）
            messagePrepareVO = messagePrepareService.add(messagePrepareVO);

            // 发送消息
            SendResult result;
            if (msgType == MessageTypeEnum.EMAIL_CODE) {
                result = messageSendCommon.messageMailSend(msgType, msgId, content);
            } else {
                result = messageSendCommon.messageSend(msgType, msgId);
            }

            log.info("告警通知发送结果: msgId={}, method={}, success={}, info={}",
                    msgId, method, result.isSuccess(), result.getInfo());

        } catch (Exception e) {
            log.error("准备并发送消息失败: msgType={}, method={}, msgId={}, error={}",
                    msgType, method, msgId, e.getMessage(), e);
            throw e;
        }
    }

    /**
     * 准备邮件消息
     */
    private void prepareEmailMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                     String title, String content, String msgId) {
        TMsgMail tMsgMail = new TMsgMail();
        tMsgMail.setId(msgId);
        tMsgMail.setMsgType(MessageTypeEnum.EMAIL_CODE);
        tMsgMail.setMsgName("告警通知");
        tMsgMail.setTitle(title);
        tMsgMail.setContent(content);
        // 设置收件人
        String email = (String) user.get("email");
        if (email != null) {
            tMsgMail.setPreviewUser(email);
        }
        messagePrepareVO.setT_Msg_Mail(tMsgMail);
    }

    /**
     * 准备短信消息
     */
    private void prepareSmsMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                   String content, int msgType, String msgId) {
        TMsgSms tMsgSms = new TMsgSms();
        tMsgSms.setId(msgId);
        tMsgSms.setMsgType(msgType);
        tMsgSms.setMsgName("告警通知");
        // 设置收件人手机号
        String phone = (String) user.get("phone");
        if (phone != null) {
            tMsgSms.setPreviewUser(phone);
        }
        // 设置短信内容（需要根据短信模板配置）
        // 这里简化处理，实际应该使用模板
        messagePrepareVO.setT_Msg_Sms(tMsgSms);
    }

    /**
     * 准备企业微信消息
     */
    private void prepareWxCpMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                     String title, String content, String msgId) {
        TMsgWxCp tMsgWxCp = new TMsgWxCp();
        tMsgWxCp.setId(msgId);
        tMsgWxCp.setMsgType(MessageTypeEnum.WX_CP_CODE);
        tMsgWxCp.setMsgName("告警通知");
        // 设置收件人
        String userId = user.get("id") != null ? user.get("id").toString() : null;
        if (userId != null) {
            tMsgWxCp.setPreviewUser(userId);
        }
        messagePrepareVO.setT_Msg_Wx_Cp(tMsgWxCp);
    }

    /**
     * 准备HTTP消息
     */
    private void prepareHttpMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                     String title, String content, String msgId) {
        TMsgHttp tMsgHttp = new TMsgHttp();
        tMsgHttp.setId(msgId);
        tMsgHttp.setMsgType(MessageTypeEnum.HTTP_CODE);
        tMsgHttp.setMsgName("告警通知");
        // HTTP消息需要配置URL等信息，这里简化处理
        messagePrepareVO.setT_Msg_Http(tMsgHttp);
    }

    /**
     * 准备钉钉消息
     */
    private void prepareDingMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                     String title, String content, String msgId) {
        TMsgDing tMsgDing = new TMsgDing();
        tMsgDing.setId(msgId);
        tMsgDing.setMsgType(MessageTypeEnum.DING_CODE);
        tMsgDing.setMsgName("告警通知");
        // 设置收件人
        String userId = user.get("id") != null ? user.get("id").toString() : null;
        if (userId != null) {
            tMsgDing.setPreviewUser(userId);
        }
        messagePrepareVO.setT_Msg_Ding(tMsgDing);
    }

    /**
     * 准备飞书消息
     */
    private void prepareFeishuMessage(MessagePrepareVO messagePrepareVO, Map<String, Object> user,
                                      String title, String content, String msgId) {
        TMsgFeishu tMsgFeishu = new TMsgFeishu();
        tMsgFeishu.setId(msgId);
        tMsgFeishu.setMsgType(MessageTypeEnum.FEISHU_CODE);
        tMsgFeishu.setMsgName("告警通知");
        tMsgFeishu.setFeishuMsgType("文本消息");
        tMsgFeishu.setTitle(title);
        tMsgFeishu.setContent(content);
        // 设置收件人（飞书通过webhook发送，这里可以设置用户标识）
        String userId = user.get("id") != null ? user.get("id").toString() : null;
        if (userId != null) {
            tMsgFeishu.setPreviewUser(userId);
        }
        // 设置webhook（可以从用户信息或配置中获取）
        String webhook = (String) user.get("webhook");
        if (webhook != null) {
            tMsgFeishu.setWebHook(webhook);
        }
        messagePrepareVO.setT_Msg_Feishu(tMsgFeishu);
    }

    /**
     * 构建通知标题
     */
    private String buildNotificationTitle(AlertNotificationMessage notificationMessage) {
        return String.format("告警通知-%s", notificationMessage.getDeviceName());
    }
}

