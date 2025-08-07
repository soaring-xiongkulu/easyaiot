package com.basiclab.iot.device.controller.admin.product_event_response;

import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;
import org.springframework.security.access.prepost.PreAuthorize;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Operation;

import javax.validation.*;
import javax.servlet.http.*;
import java.util.*;
import java.io.IOException;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import static com.basiclab.iot.common.domain.CommonResult.success;

import com.basiclab.iot.common.excel.core.util.ExcelUtils;

import com.basiclab.iot.common.apilog.core.annotation.ApiAccessLog;
import static com.basiclab.iot.common.apilog.core.enums.OperateTypeEnum.*;

import com.basiclab.iot.device.controller.admin.product_event_response.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event_response.ProductEventResponseDO;
import com.basiclab.iot.device.service.product_event_response.ProductEventResponseService;

@Tag(name = "管理后台 - 产品模型事件响应")
@RestController
@RequestMapping("/product/event-response")
@Validated
public class ProductEventResponseController {

    @Resource
    private ProductEventResponseService eventResponseService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型事件响应")
    @PreAuthorize("@ss.hasPermission('product:event-response:create')")
    public CommonResult<Long> createEventResponse(@Valid @RequestBody ProductEventResponseSaveReqVO createReqVO) {
        return success(eventResponseService.createEventResponse(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型事件响应")
    @PreAuthorize("@ss.hasPermission('product:event-response:update')")
    public CommonResult<Boolean> updateEventResponse(@Valid @RequestBody ProductEventResponseSaveReqVO updateReqVO) {
        eventResponseService.updateEventResponse(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型事件响应")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:event-response:delete')")
    public CommonResult<Boolean> deleteEventResponse(@RequestParam("id") Long id) {
        eventResponseService.deleteEventResponse(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型事件响应")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:event-response:query')")
    public CommonResult<ProductEventResponseRespVO> getEventResponse(@RequestParam("id") Long id) {
        ProductEventResponseDO eventResponse = eventResponseService.getEventResponse(id);
        return success(BeanUtils.toBean(eventResponse, ProductEventResponseRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型事件响应分页")
    @PreAuthorize("@ss.hasPermission('product:event-response:query')")
    public CommonResult<PageResult<ProductEventResponseRespVO>> getEventResponsePage(@Valid ProductEventResponsePageReqVO pageReqVO) {
        PageResult<ProductEventResponseDO> pageResult = eventResponseService.getEventResponsePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductEventResponseRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型事件响应 Excel")
    @PreAuthorize("@ss.hasPermission('product:event-response:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportEventResponseExcel(@Valid ProductEventResponsePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductEventResponseDO> list = eventResponseService.getEventResponsePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型事件响应.xls", "数据", ProductEventResponseRespVO.class,
                        BeanUtils.toBean(list, ProductEventResponseRespVO.class));
    }

}