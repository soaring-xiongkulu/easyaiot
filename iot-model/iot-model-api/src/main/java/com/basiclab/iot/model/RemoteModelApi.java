package com.basiclab.iot.model;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.model.domain.model.vo.PodModelSaveReqVO;
import com.basiclab.iot.model.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@FeignClient(name = ApiConstants.NAME)
@Tag(name = "RPC服务 - 模型管理")
public interface RemoteModelApi {

    String PREFIX = ApiConstants.PREFIX + "/model";

    @PostMapping(PREFIX + "/save-pt-model")
    @Operation(summary = "保存PT模型及训练结果")
    CommonResult<Integer> savePtModel(@RequestBody PodModelSaveReqVO saveReqVO);
}