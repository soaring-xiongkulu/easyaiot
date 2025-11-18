package com.basiclab.iot.infra.api.logger;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.infra.api.logger.dto.ApiErrorLogCreateReqDTO;
import com.basiclab.iot.infra.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import javax.validation.Valid;

/**
 * ApiErrorLogApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(name = ApiConstants.NAME) // TODO BasicLab：fallbackFact
@Tag(name = "RPC 服务 - API 异常日志")
public interface ApiErrorLogApi {

    String PREFIX = ApiConstants.PREFIX + "/api-error-log";

    @PostMapping(PREFIX + "/create")
    @Operation(summary = "创建 API 异常日志")
    CommonResult<Boolean> createApiErrorLog(@Valid @RequestBody ApiErrorLogCreateReqDTO createDTO);

}
