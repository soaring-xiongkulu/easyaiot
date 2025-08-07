package com.basiclab.iot.device.controller.admin.device_group;

import com.basiclab.iot.device.dal.dataobject.device_group.DeviceGroupDO;
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

import com.basiclab.iot.device.controller.admin.device_group.vo.*;
import com.basiclab.iot.device.service.device_group.DeviceGroupService;

@Tag(name = "管理后台 - 设备分组")
@RestController
@RequestMapping("/device/group")
@Validated
public class DeviceGroupController {

    @Resource
    private DeviceGroupService groupService;

    @PostMapping("/create")
    @Operation(summary = "创建设备分组")
    @PreAuthorize("@ss.hasPermission('device:group:create')")
    public CommonResult<Long> createGroup(@Valid @RequestBody DeviceGroupSaveReqVO createReqVO) {
        return success(groupService.createGroup(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新设备分组")
    @PreAuthorize("@ss.hasPermission('device:group:update')")
    public CommonResult<Boolean> updateGroup(@Valid @RequestBody DeviceGroupSaveReqVO updateReqVO) {
        groupService.updateGroup(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除设备分组")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('device:group:delete')")
    public CommonResult<Boolean> deleteGroup(@RequestParam("id") Long id) {
        groupService.deleteGroup(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得设备分组")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('device:group:query')")
    public CommonResult<DeviceGroupRespVO> getGroup(@RequestParam("id") Long id) {
        DeviceGroupDO group = groupService.getGroup(id);
        return success(BeanUtils.toBean(group, DeviceGroupRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得设备分组分页")
    @PreAuthorize("@ss.hasPermission('device:group:query')")
    public CommonResult<PageResult<DeviceGroupRespVO>> getGroupPage(@Valid DeviceGroupPageReqVO pageReqVO) {
        PageResult<DeviceGroupDO> pageResult = groupService.getGroupPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DeviceGroupRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出设备分组 Excel")
    @PreAuthorize("@ss.hasPermission('device:group:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportGroupExcel(@Valid DeviceGroupPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DeviceGroupDO> list = groupService.getGroupPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "设备分组.xls", "数据", DeviceGroupRespVO.class,
                        BeanUtils.toBean(list, DeviceGroupRespVO.class));
    }

}