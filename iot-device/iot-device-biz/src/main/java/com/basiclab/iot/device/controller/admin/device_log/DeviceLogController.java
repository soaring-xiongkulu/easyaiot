package com.basiclab.iot.device.controller.admin.device_log;

import com.basiclab.iot.device.dal.dataobject.device_log.DeviceLogDO;
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

import com.basiclab.iot.device.controller.admin.device_log.vo.*;
import com.basiclab.iot.device.service.device_log.DeviceLogService;

@Tag(name = "管理后台 - 设备日志")
@RestController
@RequestMapping("/device/log")
@Validated
public class DeviceLogController {

    @Resource
    private DeviceLogService logService;

    @PostMapping("/create")
    @Operation(summary = "创建设备日志")
    @PreAuthorize("@ss.hasPermission('device:log:create')")
    public CommonResult<Long> createLog(@Valid @RequestBody DeviceLogSaveReqVO createReqVO) {
        return success(logService.createLog(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新设备日志")
    @PreAuthorize("@ss.hasPermission('device:log:update')")
    public CommonResult<Boolean> updateLog(@Valid @RequestBody DeviceLogSaveReqVO updateReqVO) {
        logService.updateLog(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除设备日志")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('device:log:delete')")
    public CommonResult<Boolean> deleteLog(@RequestParam("id") Long id) {
        logService.deleteLog(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得设备日志")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('device:log:query')")
    public CommonResult<DeviceLogRespVO> getLog(@RequestParam("id") Long id) {
        DeviceLogDO log = logService.getLog(id);
        return success(BeanUtils.toBean(log, DeviceLogRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得设备日志分页")
    @PreAuthorize("@ss.hasPermission('device:log:query')")
    public CommonResult<PageResult<DeviceLogRespVO>> getLogPage(@Valid DeviceLogPageReqVO pageReqVO) {
        PageResult<DeviceLogDO> pageResult = logService.getLogPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DeviceLogRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出设备日志 Excel")
    @PreAuthorize("@ss.hasPermission('device:log:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportLogExcel(@Valid DeviceLogPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DeviceLogDO> list = logService.getLogPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "设备日志.xls", "数据", DeviceLogRespVO.class,
                        BeanUtils.toBean(list, DeviceLogRespVO.class));
    }

}