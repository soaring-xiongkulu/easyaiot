package com.basiclab.iot.system.api.notify;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.api.notify.dto.NotifyTemplateRespDTO;
import com.basiclab.iot.system.dal.dataobject.notify.NotifyTemplateDO;
import com.basiclab.iot.system.service.notify.NotifyTemplateService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * NotifyTemplateApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController // 提供 RESTful API 接口，给 Feign 调用
@Validated
public class NotifyTemplateApiImpl implements NotifyTemplateApi {

    @Resource
    private NotifyTemplateService notifyTemplateService;

    @Override
    public CommonResult<List<NotifyTemplateRespDTO>> listByType(Integer type) {
        List<NotifyTemplateDO> templates = notifyTemplateService.listByType(type);
        return success(BeanUtils.toBean(templates, NotifyTemplateRespDTO.class));
    }

    @Override
    public CommonResult<NotifyTemplateRespDTO> getTemplate(Long id) {
        NotifyTemplateDO template = notifyTemplateService.getNotifyTemplate(id);
        return success(BeanUtils.toBean(template, NotifyTemplateRespDTO.class));
    }
}

