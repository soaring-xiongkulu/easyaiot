package com.basiclab.iot.device.controller.admin.product_type;

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

import com.basiclab.iot.device.controller.admin.product_type.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_type.ProductTypeDO;
import com.basiclab.iot.device.service.product_type.ProductTypeService;

@Tag(name = "管理后台 - 产品分类")
@RestController
@RequestMapping("/product/type")
@Validated
public class ProductTypeController {

    @Resource
    private ProductTypeService typeService;

    @PostMapping("/create")
    @Operation(summary = "创建产品分类")
    @PreAuthorize("@ss.hasPermission('product:type:create')")
    public CommonResult<Long> createType(@Valid @RequestBody ProductTypeSaveReqVO createReqVO) {
        return success(typeService.createType(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品分类")
    @PreAuthorize("@ss.hasPermission('product:type:update')")
    public CommonResult<Boolean> updateType(@Valid @RequestBody ProductTypeSaveReqVO updateReqVO) {
        typeService.updateType(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品分类")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:type:delete')")
    public CommonResult<Boolean> deleteType(@RequestParam("id") Long id) {
        typeService.deleteType(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品分类")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:type:query')")
    public CommonResult<ProductTypeRespVO> getType(@RequestParam("id") Long id) {
        ProductTypeDO type = typeService.getType(id);
        return success(BeanUtils.toBean(type, ProductTypeRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品分类分页")
    @PreAuthorize("@ss.hasPermission('product:type:query')")
    public CommonResult<PageResult<ProductTypeRespVO>> getTypePage(@Valid ProductTypePageReqVO pageReqVO) {
        PageResult<ProductTypeDO> pageResult = typeService.getTypePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductTypeRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品分类 Excel")
    @PreAuthorize("@ss.hasPermission('product:type:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportTypeExcel(@Valid ProductTypePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductTypeDO> list = typeService.getTypePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品分类.xls", "数据", ProductTypeRespVO.class,
                        BeanUtils.toBean(list, ProductTypeRespVO.class));
    }

}