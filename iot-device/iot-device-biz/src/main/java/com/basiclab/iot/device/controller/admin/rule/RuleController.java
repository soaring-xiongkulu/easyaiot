package com.basiclab.iot.device.controller.admin.rule;

import com.basiclab.iot.device.controller.admin.rule.vo.RulePageReqVO;
import com.basiclab.iot.device.controller.admin.rule.vo.RuleRespVO;
import com.basiclab.iot.device.controller.admin.rule.vo.RuleSaveReqVO;
import com.basiclab.iot.device.dal.dataobject.rule.RuleDO;
import com.basiclab.iot.device.service.rule.RuleService;
import com.basiclab.iot.common.apilog.core.annotation.ApiAccessLog;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.common.excel.core.util.ExcelUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.apilog.core.enums.OperateTypeEnum.EXPORT;
import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - 规则信息")
@RestController
@RequestMapping("/rule/")
@Validated
public class RuleController {

    @Resource
    private RuleService ruleService;

    @PostMapping("/create")
    @Operation(summary = "创建规则信息")
    @PreAuthorize("@ss.hasPermission('rule::create')")
    public CommonResult<Long> create(@Valid @RequestBody RuleSaveReqVO createReqVO) {
        return success(ruleService.create(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新规则信息")
    @PreAuthorize("@ss.hasPermission('rule::update')")
    public CommonResult<Boolean> update(@Valid @RequestBody RuleSaveReqVO updateReqVO) {
        ruleService.update(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除规则信息")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('rule::delete')")
    public CommonResult<Boolean> delete(@RequestParam("id") Long id) {
        ruleService.delete(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得规则信息")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('rule::query')")
    public CommonResult<RuleRespVO> get(@RequestParam("id") Long id) {
        RuleDO ruleDO = ruleService.get(id);
        return success(BeanUtils.toBean(ruleDO, RuleRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得规则信息分页")
    @PreAuthorize("@ss.hasPermission('rule::query')")
    public CommonResult<PageResult<RuleRespVO>> getPage(@Valid RulePageReqVO pageReqVO) {
        PageResult<RuleDO> pageResult = ruleService.getPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, RuleRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出规则信息 Excel")
    @PreAuthorize("@ss.hasPermission('rule::export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportExcel(@Valid RulePageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<RuleDO> list = ruleService.getPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "规则信息.xls", "数据", RuleRespVO.class,
                        BeanUtils.toBean(list, RuleRespVO.class));
    }

}