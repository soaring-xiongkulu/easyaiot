package com.basiclab.iot.device.controller.admin.product_event;

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

import com.basiclab.iot.device.controller.admin.product_event.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_event.ProductEventDO;
import com.basiclab.iot.device.service.product_event.ProductEventService;

@Tag(name = "管理后台 - 产品模型事件")
@RestController
@RequestMapping("/product/event")
@Validated
public class ProductEventController {

    @Resource
    private ProductEventService eventService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型事件")
    @PreAuthorize("@ss.hasPermission('product:event:create')")
    public CommonResult<Long> createEvent(@Valid @RequestBody ProductEventSaveReqVO createReqVO) {
        return success(eventService.createEvent(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型事件")
    @PreAuthorize("@ss.hasPermission('product:event:update')")
    public CommonResult<Boolean> updateEvent(@Valid @RequestBody ProductEventSaveReqVO updateReqVO) {
        eventService.updateEvent(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型事件")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:event:delete')")
    public CommonResult<Boolean> deleteEvent(@RequestParam("id") Long id) {
        eventService.deleteEvent(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型事件")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:event:query')")
    public CommonResult<ProductEventRespVO> getEvent(@RequestParam("id") Long id) {
        ProductEventDO event = eventService.getEvent(id);
        return success(BeanUtils.toBean(event, ProductEventRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型事件分页")
    @PreAuthorize("@ss.hasPermission('product:event:query')")
    public CommonResult<PageResult<ProductEventRespVO>> getEventPage(@Valid ProductEventPageReqVO pageReqVO) {
        PageResult<ProductEventDO> pageResult = eventService.getEventPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductEventRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型事件 Excel")
    @PreAuthorize("@ss.hasPermission('product:event:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportEventExcel(@Valid ProductEventPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductEventDO> list = eventService.getEventPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型事件.xls", "数据", ProductEventRespVO.class,
                        BeanUtils.toBean(list, ProductEventRespVO.class));
    }

}