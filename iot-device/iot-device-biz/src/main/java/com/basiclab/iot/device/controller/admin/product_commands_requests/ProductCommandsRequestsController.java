package com.basiclab.iot.device.controller.admin.product_commands_requests;

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

import com.basiclab.iot.device.controller.admin.product_commands_requests.vo.*;
import com.basiclab.iot.device.dal.dataobject.product_commands_requests.ProductCommandsRequestsDO;
import com.basiclab.iot.device.service.product_commands_requests.ProductCommandsRequestsService;

@Tag(name = "管理后台 - 产品模型设备下发服务命令属性")
@RestController
@RequestMapping("/product/commands-requests")
@Validated
public class ProductCommandsRequestsController {

    @Resource
    private ProductCommandsRequestsService commandsRequestsService;

    @PostMapping("/create")
    @Operation(summary = "创建产品模型设备下发服务命令属性")
    @PreAuthorize("@ss.hasPermission('product:commands-requests:create')")
    public CommonResult<Long> createCommandsRequests(@Valid @RequestBody ProductCommandsRequestsSaveReqVO createReqVO) {
        return success(commandsRequestsService.createCommandsRequests(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新产品模型设备下发服务命令属性")
    @PreAuthorize("@ss.hasPermission('product:commands-requests:update')")
    public CommonResult<Boolean> updateCommandsRequests(@Valid @RequestBody ProductCommandsRequestsSaveReqVO updateReqVO) {
        commandsRequestsService.updateCommandsRequests(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除产品模型设备下发服务命令属性")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('product:commands-requests:delete')")
    public CommonResult<Boolean> deleteCommandsRequests(@RequestParam("id") Long id) {
        commandsRequestsService.deleteCommandsRequests(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得产品模型设备下发服务命令属性")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('product:commands-requests:query')")
    public CommonResult<ProductCommandsRequestsRespVO> getCommandsRequests(@RequestParam("id") Long id) {
        ProductCommandsRequestsDO commandsRequests = commandsRequestsService.getCommandsRequests(id);
        return success(BeanUtils.toBean(commandsRequests, ProductCommandsRequestsRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得产品模型设备下发服务命令属性分页")
    @PreAuthorize("@ss.hasPermission('product:commands-requests:query')")
    public CommonResult<PageResult<ProductCommandsRequestsRespVO>> getCommandsRequestsPage(@Valid ProductCommandsRequestsPageReqVO pageReqVO) {
        PageResult<ProductCommandsRequestsDO> pageResult = commandsRequestsService.getCommandsRequestsPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, ProductCommandsRequestsRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出产品模型设备下发服务命令属性 Excel")
    @PreAuthorize("@ss.hasPermission('product:commands-requests:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportCommandsRequestsExcel(@Valid ProductCommandsRequestsPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<ProductCommandsRequestsDO> list = commandsRequestsService.getCommandsRequestsPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "产品模型设备下发服务命令属性.xls", "数据", ProductCommandsRequestsRespVO.class,
                        BeanUtils.toBean(list, ProductCommandsRequestsRespVO.class));
    }

}