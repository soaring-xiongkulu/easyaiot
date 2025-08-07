package com.basiclab.iot.device.controller.admin.rule_conditions;

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

import com.basiclab.iot.device.controller.admin.rule_conditions.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_conditions.RuleConditionsDO;
import com.basiclab.iot.device.service.rule_conditions.RuleConditionsService;

@Tag(name = "管理后台 - 规则条件")
@RestController
@RequestMapping("/rule/conditions")
@Validated
public class RuleConditionsController {

    @Resource
    private RuleConditionsService conditionsService;

    @PostMapping("/create")
    @Operation(summary = "创建规则条件")
    @PreAuthorize("@ss.hasPermission('rule:conditions:create')")
    public CommonResult<Long> createConditions(@Valid @RequestBody RuleConditionsSaveReqVO createReqVO) {
        return success(conditionsService.createConditions(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新规则条件")
    @PreAuthorize("@ss.hasPermission('rule:conditions:update')")
    public CommonResult<Boolean> updateConditions(@Valid @RequestBody RuleConditionsSaveReqVO updateReqVO) {
        conditionsService.updateConditions(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除规则条件")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('rule:conditions:delete')")
    public CommonResult<Boolean> deleteConditions(@RequestParam("id") Long id) {
        conditionsService.deleteConditions(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得规则条件")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('rule:conditions:query')")
    public CommonResult<RuleConditionsRespVO> getConditions(@RequestParam("id") Long id) {
        RuleConditionsDO conditions = conditionsService.getConditions(id);
        return success(BeanUtils.toBean(conditions, RuleConditionsRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得规则条件分页")
    @PreAuthorize("@ss.hasPermission('rule:conditions:query')")
    public CommonResult<PageResult<RuleConditionsRespVO>> getConditionsPage(@Valid RuleConditionsPageReqVO pageReqVO) {
        PageResult<RuleConditionsDO> pageResult = conditionsService.getConditionsPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, RuleConditionsRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出规则条件 Excel")
    @PreAuthorize("@ss.hasPermission('rule:conditions:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportConditionsExcel(@Valid RuleConditionsPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<RuleConditionsDO> list = conditionsService.getConditionsPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "规则条件.xls", "数据", RuleConditionsRespVO.class,
                        BeanUtils.toBean(list, RuleConditionsRespVO.class));
    }

}