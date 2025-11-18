package com.basiclab.iot.system.framework.sms.core.client;

import com.basiclab.iot.common.core.KeyValue;
import com.basiclab.iot.system.framework.sms.core.client.dto.SmsReceiveRespDTO;
import com.basiclab.iot.system.framework.sms.core.client.dto.SmsSendRespDTO;
import com.basiclab.iot.system.framework.sms.core.client.dto.SmsTemplateRespDTO;

import java.util.List;

/**
 * SmsClient
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface SmsClient {

    /**
     * 获得渠道编号
     *
     * @return 渠道编号
     */
    Long getId();

    /**
     * 发送消息
     *
     * @param logId 日志编号
     * @param mobile 手机号
     * @param apiTemplateId 短信 API 的模板编号
     * @param templateParams 短信模板参数。通过 List 数组，保证参数的顺序
     * @return 短信发送结果
     */
    SmsSendRespDTO sendSms(Long logId, String mobile, String apiTemplateId,
                           List<KeyValue<String, Object>> templateParams) throws Throwable;

    /**
     * 解析接收短信的接收结果
     *
     * @param text 结果
     * @return 结果内容
     * @throws Throwable 当解析 text 发生异常时，则会抛出异常
     */
    List<SmsReceiveRespDTO> parseSmsReceiveStatus(String text) throws Throwable;

    /**
     * 查询指定的短信模板
     *
     * @param apiTemplateId 短信 API 的模板编号
     * @return 短信模板
     */
    SmsTemplateRespDTO getSmsTemplate(String apiTemplateId) throws Throwable;

}
