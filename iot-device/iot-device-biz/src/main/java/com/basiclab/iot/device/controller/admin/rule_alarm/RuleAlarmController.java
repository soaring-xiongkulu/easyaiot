package com.basiclab.iot.device.controller.admin.rule_alarm;

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

import com.basiclab.iot.device.controller.admin.rule_alarm.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm.RuleAlarmDO;
import com.basiclab.iot.device.service.rule_alarm.RuleAlarmService;

@Tag(name = "管理后台 - 规则告警")
@RestController
@RequestMapping("/rule/alarm")
@Validated
public class RuleAlarmController {

    @Resource
    private RuleAlarmService alarmService;

    @PostMapping("/create")
    @Operation(summary = "创建规则告警")
    @PreAuthorize("@ss.hasPermission('rule:alarm:create')")
    public CommonResult<Long> createAlarm(@Valid @RequestBody RuleAlarmSaveReqVO createReqVO) {
        return success(alarmService.createAlarm(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新规则告警")
    @PreAuthorize("@ss.hasPermission('rule:alarm:update')")
    public CommonResult<Boolean> updateAlarm(@Valid @RequestBody RuleAlarmSaveReqVO updateReqVO) {
        alarmService.updateAlarm(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除规则告警")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('rule:alarm:delete')")
    public CommonResult<Boolean> deleteAlarm(@RequestParam("id") Long id) {
        alarmService.deleteAlarm(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得规则告警")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('rule:alarm:query')")
    public CommonResult<RuleAlarmRespVO> getAlarm(@RequestParam("id") Long id) {
        RuleAlarmDO alarm = alarmService.getAlarm(id);
        return success(BeanUtils.toBean(alarm, RuleAlarmRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得规则告警分页")
    @PreAuthorize("@ss.hasPermission('rule:alarm:query')")
    public CommonResult<PageResult<RuleAlarmRespVO>> getAlarmPage(@Valid RuleAlarmPageReqVO pageReqVO) {
        PageResult<RuleAlarmDO> pageResult = alarmService.getAlarmPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, RuleAlarmRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出规则告警 Excel")
    @PreAuthorize("@ss.hasPermission('rule:alarm:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportAlarmExcel(@Valid RuleAlarmPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<RuleAlarmDO> list = alarmService.getAlarmPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "规则告警.xls", "数据", RuleAlarmRespVO.class,
                        BeanUtils.toBean(list, RuleAlarmRespVO.class));
    }

}