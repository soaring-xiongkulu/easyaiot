package com.basiclab.iot.system.service.sms;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplatePageReqVO;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplateSaveReqVO;
import com.basiclab.iot.system.dal.dataobject.sms.SmsTemplateDO;

import javax.validation.Valid;
import java.util.Map;

/**
 * SmsTemplateService
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface SmsTemplateService {

    /**
     * 创建短信模板
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createSmsTemplate(@Valid SmsTemplateSaveReqVO createReqVO);

    /**
     * 更新短信模板
     *
     * @param updateReqVO 更新信息
     */
    void updateSmsTemplate(@Valid SmsTemplateSaveReqVO updateReqVO);

    /**
     * 删除短信模板
     *
     * @param id 编号
     */
    void deleteSmsTemplate(Long id);

    /**
     * 获得短信模板
     *
     * @param id 编号
     * @return 短信模板
     */
    SmsTemplateDO getSmsTemplate(Long id);

    /**
     * 获得短信模板，从缓存中
     *
     * @param code 模板编码
     * @return 短信模板
     */
    SmsTemplateDO getSmsTemplateByCodeFromCache(String code);

    /**
     * 获得短信模板分页
     *
     * @param pageReqVO 分页查询
     * @return 短信模板分页
     */
    PageResult<SmsTemplateDO> getSmsTemplatePage(SmsTemplatePageReqVO pageReqVO);

    /**
     * 获得指定短信渠道下的短信模板数量
     *
     * @param channelId 短信渠道编号
     * @return 数量
     */
    Long getSmsTemplateCountByChannelId(Long channelId);

    /**
     * 格式化短信内容
     *
     * @param content 短信模板的内容
     * @param params 内容的参数
     * @return 格式化后的内容
     */
    String formatSmsTemplateContent(String content, Map<String, Object> params);

}
