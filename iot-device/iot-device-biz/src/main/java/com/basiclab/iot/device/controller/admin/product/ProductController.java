package com.basiclab.iot.device.controller.admin.product;

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

import com.basiclab.iot.device.controller.admin.product.vo.*;
import com.basiclab.iot.device.dal.dataobject.product.Product;
import com.basiclab.iot.device.service.product.ProductService;

@Tag(name = "管理后台 - 产品")
@RestController
@RequestMapping("/product/")
@Validated
public class ProductController {

    @Resource
    private ProductService ProductService;

    @PostMapping("/create")
    @Operation(summary = "创建产品")
    @PreAuthorize("@ss.hasPermission('product::create')")
    public CommonResult<Long> create(@Valid @RequestBody ProductSaveReqVO createReqVO) {
        return success(ProductService.create(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品")
    @PreAuthorize("@ss.hasPermission('product::update')")
    public CommonResult<Boolean> update(@Valid @RequestBody ProductSaveReqVO updateReqVO) {
        ProductService.update(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product::delete')")
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        ProductService.delete(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product::query')")
    public CommonResult<ProductRespVO> get(@RequestParam("id") Long id) {
        Product productDO  = ProductService.get(id);
        return success(BeanUtils.toBean(productDO, ProductRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品分页")
    @PreAuthorize("@ss.hasPermission('product::query')")
    public CommonResult<PageResult<ProductRespVO>> getPage(@Valid ProductPageReqVO pageReqVO) {
        PageResult<Product> pageResult = ProductService.getPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品 Excel")
    @PreAuthorize("@ss.hasPermission('product::export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportExcel(@Valid ProductPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<Product> list = ProductService.getPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品.xls", "数据", ProductRespVO.class,
                        BeanUtils.toBean(list, ProductRespVO.class));
    }

}