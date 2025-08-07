package com.basiclab.iot.device.controller.admin.ota_tasks;

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

import com.basiclab.iot.device.controller.admin.ota_tasks.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_tasks.OtaTasksDO;
import com.basiclab.iot.device.service.ota_tasks.OtaTasksService;

@Tag(name = "管理后台 - OTA升级任务")
@RestController
@RequestMapping("/ota/tasks")
@Validated
public class OtaTasksController {

    @Resource
    private OtaTasksService tasksService;

    @PostMapping("/create")
    @Operation(summary = "创建OTA升级任务")
    @PreAuthorize("@ss.hasPermission('ota:tasks:create')")
    public CommonResult<Long> createTasks(@Valid @RequestBody OtaTasksSaveReqVO createReqVO) {
        return success(tasksService.createTasks(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新OTA升级任务")
    @PreAuthorize("@ss.hasPermission('ota:tasks:update')")
    public CommonResult<Boolean> updateTasks(@Valid @RequestBody OtaTasksSaveReqVO updateReqVO) {
        tasksService.updateTasks(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除OTA升级任务")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('ota:tasks:delete')")
    public CommonResult<Boolean> deleteTasks(@RequestParam("id") Long id) {
        tasksService.deleteTasks(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得OTA升级任务")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('ota:tasks:query')")
    public CommonResult<OtaTasksRespVO> getTasks(@RequestParam("id") Long id) {
        OtaTasksDO tasks = tasksService.getTasks(id);
        return success(BeanUtils.toBean(tasks, OtaTasksRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得OTA升级任务分页")
    @PreAuthorize("@ss.hasPermission('ota:tasks:query')")
    public CommonResult<PageResult<OtaTasksRespVO>> getTasksPage(@Valid OtaTasksPageReqVO pageReqVO) {
        PageResult<OtaTasksDO> pageResult = tasksService.getTasksPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, OtaTasksRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出OTA升级任务 Excel")
    @PreAuthorize("@ss.hasPermission('ota:tasks:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportTasksExcel(@Valid OtaTasksPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<OtaTasksDO> list = tasksService.getTasksPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "OTA升级任务.xls", "数据", OtaTasksRespVO.class,
                        BeanUtils.toBean(list, OtaTasksRespVO.class));
    }

}