package com.basiclab.iot.device.controller.admin.device;

import com.basiclab.iot.device.common.BaseController;
import com.basiclab.iot.device.common.CommonResult;
import com.basiclab.iot.device.common.TableDataInfo;
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
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.common.excel.core.util.ExcelUtils;

import com.basiclab.iot.common.apilog.core.annotation.ApiAccessLog;
import static com.basiclab.iot.common.apilog.core.enums.OperateTypeEnum.*;
import static com.github.pagehelper.page.PageMethod.startPage;

import com.basiclab.iot.device.controller.admin.device.vo.*;
import com.basiclab.iot.device.dal.dataobject.device.DeviceDO;
import com.basiclab.iot.device.service.device.DeviceService;

@Tag(name = "管理后台 - 设备")
@RestController
@RequestMapping("/device/")
@Validated
public class DeviceController extends BaseController {

    @Resource
    private DeviceService deviceService;

    @PostMapping("/create")
    @Operation(summary = "创建设备")
    @PreAuthorize("@ss.hasPermission('device:device:create')")
    public CommonResult create(@Valid @RequestBody DeviceSaveReqVO createReqVO) {
        return success(deviceService.create(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新设备")
    @PreAuthorize("@ss.hasPermission('device:device:update')")
    public CommonResult update(@Valid @RequestBody DeviceSaveReqVO updateReqVO) {
        deviceService.update(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除设备")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('device:device:delete')")
    public CommonResult delete(@RequestParam("id") Long id) {
        deviceService.delete(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得设备")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('device:device:query')")
    public CommonResult get(@RequestParam("id") Long id) {
        DeviceDO deviceDO  = deviceService.get(id);
        return success(BeanUtils.toBean(deviceDO, DeviceRespVO.class));
    }

    /**
     * 查询设备管理列表
     */
    @PreAuthorize("@ss.hasPermission('link:device:list')")
    @GetMapping("/list")
    public TableDataInfo list(Device device) {
        startPage();
        List<Device> list = deviceService.selectDeviceList(device);
        return getDataTable(list);
    }

    @GetMapping("/page")
    @Operation(summary = "获得设备分页")
    @PreAuthorize("@ss.hasPermission('device:device:query')")
    public CommonResult getPage(@Valid DevicePageReqVO pageReqVO) {
        PageResult<DeviceDO> pageResult = deviceService.getPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DeviceRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出设备 Excel")
    @PreAuthorize("@ss.hasPermission('device:device:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportExcel(@Valid DevicePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DeviceDO> list = deviceService.getPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "设备.xls", "数据", DeviceRespVO.class,
                        BeanUtils.toBean(list, DeviceRespVO.class));
    }

}