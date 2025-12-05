package com.basiclab.iot.system.api.mail;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.system.api.mail.dto.MailTemplateRespDTO;
import com.basiclab.iot.system.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

/**
 * MailTemplateApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(name = ApiConstants.NAME)
@Tag(name = "RPC 服务 - 邮件模板")
public interface MailTemplateApi {

    String PREFIX = ApiConstants.PREFIX + "/mail-template";

    @GetMapping(PREFIX + "/simple-list")
    @Operation(summary = "获得邮件模版精简列表")
    CommonResult<List<MailTemplateRespDTO>> getSimpleTemplateList();
}

