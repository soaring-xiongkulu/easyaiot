package com.basiclab.iot.device.controller.admin.product_template;

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

import com.basiclab.iot.device.controller.admin.product_template.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_template.ProductTemplateDO;
import com.basiclab.iot.device.service.product_template.TemplateService;

@Tag(name = "管理后台 - 产品模板")
@RestController
@RequestMapping("/product/template")
@Validated
public class ProductTemplateController {

    @Resource
    private TemplateService templateService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模板")
    @PreAuthorize("@ss.hasPermission('product:template:create')")
    public CommonResult<Long> createTemplate(@Valid @RequestBody ProductTemplateSaveReqVO createReqVO) {
        return success(templateService.createTemplate(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模板")
    @PreAuthorize("@ss.hasPermission('product:template:update')")
    public CommonResult<Boolean> updateTemplate(@Valid @RequestBody ProductTemplateSaveReqVO updateReqVO) {
        templateService.updateTemplate(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模板")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:template:delete')")
    public CommonResult<Boolean> deleteTemplate(@RequestParam("id") Long id) {
        templateService.deleteTemplate(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模板")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:template:query')")
    public CommonResult<ProductTemplateRespVO> getTemplate(@RequestParam("id") Long id) {
        ProductTemplateDO template = templateService.getTemplate(id);
        return success(BeanUtils.toBean(template, ProductTemplateRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模板分页")
    @PreAuthorize("@ss.hasPermission('product:template:query')")
    public CommonResult<PageResult<ProductTemplateRespVO>> getTemplatePage(@Valid ProductTemplatePageReqVO pageReqVO) {
        PageResult<ProductTemplateDO> pageResult = templateService.getTemplatePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductTemplateRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模板 Excel")
    @PreAuthorize("@ss.hasPermission('product:template:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportTemplateExcel(@Valid ProductTemplatePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductTemplateDO> list = templateService.getTemplatePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模板.xls", "数据", ProductTemplateRespVO.class,
                        BeanUtils.toBean(list, ProductTemplateRespVO.class));
    }

}