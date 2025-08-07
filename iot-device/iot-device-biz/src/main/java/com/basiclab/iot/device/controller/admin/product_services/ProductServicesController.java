package com.basiclab.iot.device.controller.admin.product_services;

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

import com.basiclab.iot.device.controller.admin.product_services.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_services.ProductServicesDO;
import com.basiclab.iot.device.service.product_services.ProductServicesService;

@Tag(name = "管理后台 - 产品模型服务")
@RestController
@RequestMapping("/product/services")
@Validated
public class ProductServicesController {

    @Resource
    private ProductServicesService servicesService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型服务")
    @PreAuthorize("@ss.hasPermission('product:services:create')")
    public CommonResult<Long> createServices(@Valid @RequestBody ProductServicesSaveReqVO createReqVO) {
        return success(servicesService.createServices(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型服务")
    @PreAuthorize("@ss.hasPermission('product:services:update')")
    public CommonResult<Boolean> updateServices(@Valid @RequestBody ProductServicesSaveReqVO updateReqVO) {
        servicesService.updateServices(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型服务")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:services:delete')")
    public CommonResult<Boolean> deleteServices(@RequestParam("id") Long id) {
        servicesService.deleteServices(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型服务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:services:query')")
    public CommonResult<ProductServicesRespVO> getServices(@RequestParam("id") Long id) {
        ProductServicesDO services = servicesService.getServices(id);
        return success(BeanUtils.toBean(services, ProductServicesRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型服务分页")
    @PreAuthorize("@ss.hasPermission('product:services:query')")
    public CommonResult<PageResult<ProductServicesRespVO>> getServicesPage(@Valid ProductServicesPageReqVO pageReqVO) {
        PageResult<ProductServicesDO> pageResult = servicesService.getServicesPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductServicesRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型服务 Excel")
    @PreAuthorize("@ss.hasPermission('product:services:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportServicesExcel(@Valid ProductServicesPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductServicesDO> list = servicesService.getServicesPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型服务.xls", "数据", ProductServicesRespVO.class,
                        BeanUtils.toBean(list, ProductServicesRespVO.class));
    }

}