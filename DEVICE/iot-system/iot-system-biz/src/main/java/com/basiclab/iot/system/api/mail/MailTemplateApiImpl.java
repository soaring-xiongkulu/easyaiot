package com.basiclab.iot.system.api.mail;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.api.mail.dto.MailTemplateRespDTO;
import com.basiclab.iot.system.dal.dataobject.mail.MailTemplateDO;
import com.basiclab.iot.system.service.mail.MailTemplateService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * MailTemplateApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController // 提供 RESTful API 接口，给 Feign 调用
@Validated
public class MailTemplateApiImpl implements MailTemplateApi {

    @Resource
    private MailTemplateService mailTemplateService;

    @Override
    public CommonResult<List<MailTemplateRespDTO>> getSimpleTemplateList() {
        List<MailTemplateDO> templates = mailTemplateService.getMailTemplateList();
        // 只返回启用的模板（status=0表示启用）
        templates = templates.stream()
                .filter(template -> template.getStatus() != null && template.getStatus() == com.basiclab.iot.common.enums.CommonStatusEnum.ENABLE.getStatus())
                .collect(java.util.stream.Collectors.toList());
        return success(BeanUtils.toBean(templates, MailTemplateRespDTO.class));
    }
}

