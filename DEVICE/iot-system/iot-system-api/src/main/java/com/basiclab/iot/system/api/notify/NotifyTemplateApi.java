package com.basiclab.iot.system.api.notify;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.system.api.notify.dto.NotifyTemplateRespDTO;
import com.basiclab.iot.system.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * NotifyTemplateApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(name = ApiConstants.NAME)
@Tag(name = "RPC 服务 - 通知模板")
public interface NotifyTemplateApi {

    String PREFIX = ApiConstants.PREFIX + "/notify-template";

    @GetMapping(PREFIX + "/list-by-type")
    @Operation(summary = "根据类型查询通知模板列表")
    CommonResult<List<NotifyTemplateRespDTO>> listByType(
            @Parameter(description = "模板类型", required = true) @RequestParam("type") Integer type
    );

    @GetMapping(PREFIX + "/get")
    @Operation(summary = "根据ID获取通知模板")
    CommonResult<NotifyTemplateRespDTO> getTemplate(
            @Parameter(description = "模板ID", required = true) @RequestParam("id") Long id
    );
}

