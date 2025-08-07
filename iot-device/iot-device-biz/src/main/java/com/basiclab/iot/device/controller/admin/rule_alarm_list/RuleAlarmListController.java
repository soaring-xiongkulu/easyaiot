package com.basiclab.iot.device.controller.admin.rule_alarm_list;

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

import com.basiclab.iot.device.controller.admin.rule_alarm_list.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm_list.RuleAlarmListDO;
import com.basiclab.iot.device.service.rule_alarm_list.RuleAlarmListService;

@Tag(name = "管理后台 - 告警列")
@RestController
@RequestMapping("/rule/alarm-list")
@Validated
public class RuleAlarmListController {

    @Resource
    private RuleAlarmListService alarmListService;

    @PostMapping("/create")
    @Operation(summary = "创建告警列")
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:create')")
    public CommonResult<Long> createAlarmList(@Valid @RequestBody RuleAlarmListSaveReqVO createReqVO) {
        return success(alarmListService.createAlarmList(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新告警列")
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:update')")
    public CommonResult<Boolean> updateAlarmList(@Valid @RequestBody RuleAlarmListSaveReqVO updateReqVO) {
        alarmListService.updateAlarmList(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除告警列")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:delete')")
    public CommonResult<Boolean> deleteAlarmList(@RequestParam("id") Long id) {
        alarmListService.deleteAlarmList(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得告警列")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:query')")
    public CommonResult<RuleAlarmListRespVO> getAlarmList(@RequestParam("id") Long id) {
        RuleAlarmListDO alarmList = alarmListService.getAlarmList(id);
        return success(BeanUtils.toBean(alarmList, RuleAlarmListRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得告警列分页")
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:query')")
    public CommonResult<PageResult<RuleAlarmListRespVO>> getAlarmListPage(@Valid RuleAlarmListPageReqVO pageReqVO) {
        PageResult<RuleAlarmListDO> pageResult = alarmListService.getAlarmListPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, RuleAlarmListRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出告警列 Excel")
    @PreAuthorize("@ss.hasPermission('rule:alarm-list:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportAlarmListExcel(@Valid RuleAlarmListPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<RuleAlarmListDO> list = alarmListService.getAlarmListPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "告警列.xls", "数据", RuleAlarmListRespVO.class,
                        BeanUtils.toBean(list, RuleAlarmListRespVO.class));
    }

}