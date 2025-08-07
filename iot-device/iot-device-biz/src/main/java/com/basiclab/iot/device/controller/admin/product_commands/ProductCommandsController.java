package com.basiclab.iot.device.controller.admin.product_commands;

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

import com.basiclab.iot.device.controller.admin.product_commands.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands.ProductCommandsDO;
import com.basiclab.iot.device.service.product_commands.ProductCommandsService;

@Tag(name = "管理后台 - 产品模型设备服务命令")
@RestController
@RequestMapping("/product/commands")
@Validated
public class ProductCommandsController {

    @Resource
    private ProductCommandsService commandsService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型设备服务命令")
    @PreAuthorize("@ss.hasPermission('product:commands:create')")
    public CommonResult<Long> createCommands(@Valid @RequestBody ProductCommandsSaveReqVO createReqVO) {
        return success(commandsService.createCommands(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型设备服务命令")
    @PreAuthorize("@ss.hasPermission('product:commands:update')")
    public CommonResult<Boolean> updateCommands(@Valid @RequestBody ProductCommandsSaveReqVO updateReqVO) {
        commandsService.updateCommands(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型设备服务命令")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:commands:delete')")
    public CommonResult<Boolean> deleteCommands(@RequestParam("id") Long id) {
        commandsService.deleteCommands(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型设备服务命令")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:commands:query')")
    public CommonResult<ProductCommandsRespVO> getCommands(@RequestParam("id") Long id) {
        ProductCommandsDO commands = commandsService.getCommands(id);
        return success(BeanUtils.toBean(commands, ProductCommandsRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型设备服务命令分页")
    @PreAuthorize("@ss.hasPermission('product:commands:query')")
    public CommonResult<PageResult<ProductCommandsRespVO>> getCommandsPage(@Valid ProductCommandsPageReqVO pageReqVO) {
        PageResult<ProductCommandsDO> pageResult = commandsService.getCommandsPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductCommandsRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型设备服务命令 Excel")
    @PreAuthorize("@ss.hasPermission('product:commands:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportCommandsExcel(@Valid ProductCommandsPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductCommandsDO> list = commandsService.getCommandsPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型设备服务命令.xls", "数据", ProductCommandsRespVO.class,
                        BeanUtils.toBean(list, ProductCommandsRespVO.class));
    }

}