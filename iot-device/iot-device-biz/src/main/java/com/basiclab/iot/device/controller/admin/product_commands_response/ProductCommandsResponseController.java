package com.basiclab.iot.device.controller.admin.product_commands_response;

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

import com.basiclab.iot.device.controller.admin.product_commands_response.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands_response.ProductCommandsResponseDO;
import com.basiclab.iot.device.service.product_commands_response.ProductCommandsResponseService;

@Tag(name = "管理后台 - 产品模型设备响应服务命令属性")
@RestController
@RequestMapping("/product/commands-response")
@Validated
public class ProductCommandsResponseController {

    @Resource
    private ProductCommandsResponseService commandsResponseService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型设备响应服务命令属性")
    @PreAuthorize("@ss.hasPermission('product:commands-response:create')")
    public CommonResult<Long> createCommandsResponse(@Valid @RequestBody ProductCommandsResponseSaveReqVO createReqVO) {
        return success(commandsResponseService.createCommandsResponse(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型设备响应服务命令属性")
    @PreAuthorize("@ss.hasPermission('product:commands-response:update')")
    public CommonResult<Boolean> updateCommandsResponse(@Valid @RequestBody ProductCommandsResponseSaveReqVO updateReqVO) {
        commandsResponseService.updateCommandsResponse(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型设备响应服务命令属性")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:commands-response:delete')")
    public CommonResult<Boolean> deleteCommandsResponse(@RequestParam("id") Long id) {
        commandsResponseService.deleteCommandsResponse(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型设备响应服务命令属性")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:commands-response:query')")
    public CommonResult<ProductCommandsResponseRespVO> getCommandsResponse(@RequestParam("id") Long id) {
        ProductCommandsResponseDO commandsResponse = commandsResponseService.getCommandsResponse(id);
        return success(BeanUtils.toBean(commandsResponse, ProductCommandsResponseRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型设备响应服务命令属性分页")
    @PreAuthorize("@ss.hasPermission('product:commands-response:query')")
    public CommonResult<PageResult<ProductCommandsResponseRespVO>> getCommandsResponsePage(@Valid ProductCommandsResponsePageReqVO pageReqVO) {
        PageResult<ProductCommandsResponseDO> pageResult = commandsResponseService.getCommandsResponsePage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductCommandsResponseRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型设备响应服务命令属性 Excel")
    @PreAuthorize("@ss.hasPermission('product:commands-response:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportCommandsResponseExcel(@Valid ProductCommandsResponsePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductCommandsResponseDO> list = commandsResponseService.getCommandsResponsePage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型设备响应服务命令属性.xls", "数据", ProductCommandsResponseRespVO.class,
                        BeanUtils.toBean(list, ProductCommandsResponseRespVO.class));
    }

}