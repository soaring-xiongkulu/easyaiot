package com.basiclab.iot.dataset;



import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagRespVO;
import com.basiclab.iot.dataset.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@FeignClient(name = ApiConstants.NAME) // 服务名称常量
@Tag(name = "RPC服务 - 数据集和数据仓标签")

/**
 * RemoteDatasetTagApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public interface RemoteDatasetTagApi {

    String PREFIX = ApiConstants.PREFIX + "/tag";

    @GetMapping(PREFIX + "/list-by-dataset")
    @Operation(summary = "根据数据集ID获取标签列表")
    CommonResult<List<DatasetTagRespVO>> listTagsByDataset(
            @Parameter(description = "数据集ID", required = true)
            @RequestParam("datasetId") Long datasetId);
}