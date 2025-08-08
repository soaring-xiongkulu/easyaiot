package com.basiclab.iot.rule.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;


import com.basiclab.iot.common.annotations.PreAuthorize;
import com.basiclab.iot.rule.domain.Rule;
import com.basiclab.iot.rule.domain.RuleConditions;
import com.basiclab.iot.rule.domain.model.RuleConditionsModel;
import com.basiclab.iot.rule.domain.model.vo.RuleConditionActionVo;
import com.basiclab.iot.rule.domain.model.vo.RuleConditionVo;
import com.basiclab.iot.rule.service.RuleConditionsService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;
import java.util.Objects;

@Tag(name  = "规则条件管理")
@RestController
@RequestMapping("/ruleConditions")
public class RuleConditionsController extends BaseController {

    @Resource
    private RuleConditionsService ruleConditionsService;


//    // @PreAuthorize(hasPermi = "rule:rule:list")
    @GetMapping("/list")
    @ApiOperation("触发条件列表")
    public TableDataInfo list(RuleConditions ruleConditions) {
        LambdaQueryWrapper<RuleConditions> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Objects.nonNull( ruleConditions.getRuleId()) ,RuleConditions::getRuleId, ruleConditions.getRuleId());
        queryWrapper.eq(Objects.nonNull(ruleConditions.getConditionType()),RuleConditions::getConditionType, ruleConditions.getConditionType());
        queryWrapper.eq(Objects.nonNull( ruleConditions.getConditionScheme()) && !ruleConditions.getConditionScheme().isEmpty(),RuleConditions::getConditionScheme, ruleConditions.getConditionScheme());
        queryWrapper.eq(Objects.nonNull(ruleConditions.getId()),RuleConditions::getId, ruleConditions.getId());
        queryWrapper.eq(Objects.nonNull(ruleConditions.getCreateBy()) && !ruleConditions.getCreateBy().isEmpty(),RuleConditions::getCreateBy, ruleConditions.getCreateBy());
        queryWrapper.eq(Objects.nonNull(ruleConditions.getCreateTime()),RuleConditions::getCreateTime, ruleConditions.getCreateTime());
        queryWrapper.eq(Objects.nonNull( ruleConditions.getUpdateBy()) && !ruleConditions.getUpdateBy().isEmpty(),RuleConditions::getUpdateBy, ruleConditions.getUpdateBy());
        queryWrapper.eq(Objects.nonNull( ruleConditions.getUpdateTime()),RuleConditions::getUpdateTime, ruleConditions.getUpdateTime());
        List<RuleConditions> list = ruleConditionsService.list(queryWrapper);
        return getDataTable(list);
    }

    /**
     * 批量添加触发条件
     */
    @NoRepeatSubmit
//    // @PreAuthorize(hasPermi = "rule:ruleConditions:add")
    //@Log(title = "触发条件", businessType = BusinessType.INSERT)
    @PostMapping("/batchInsert")
    @ApiOperation("批量添加触发条件")
    public AjaxResult add(@RequestBody List<RuleConditions> ruleConditions) {
        return AjaxResult.success(ruleConditionsService.batchInsert(ruleConditions));
    }

    /**
     * 新增触发条件
     */
    @NoRepeatSubmit
//    // @PreAuthorize(hasPermi = "rule:ruleConditions:edit")
    //@Log(title = "规则条件", businessType = BusinessType.UPDATE)
    @PutMapping
    @ApiOperation("批量更新触发条件")
    public AjaxResult edit(@RequestBody List<RuleConditions> ruleConditions) {
        return toAjax(ruleConditionsService.updateBatch(ruleConditions));
    }
    /**
     * 新增触发条件
     */
    @NoRepeatSubmit
//    // @PreAuthorize(hasPermi = "rule:ruleConditions:edit")
    //@Log(title = "触发条件", businessType = BusinessType.UPDATE)
    @PutMapping("/batchEdit")
    @ApiOperation("编辑触发条件")
    public AjaxResult batchEdit(@RequestBody List<RuleConditions> ruleConditions) {
        return toAjax(ruleConditionsService.updateBatchSelective(ruleConditions));
    }

    /**
     * 批量删除触发条件
     * @param ids
     * @return
     */
//    // @PreAuthorize(hasPermi = "link:ruleConditions:remove")
    //@Log(title = "触发条件", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    @ApiOperation("批量删除触发条件")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(ruleConditionsService.deleteBatchByIds(ids));
    }



    /**
     * 保存或更新规则条件和动作
     */
    @NoRepeatSubmit
//    // @PreAuthorize(hasPermi = "rule:ruleConditionVo:add")
    //@Log(title = "保存或更新规则条件和动作", businessType = BusinessType.INSERT)
    @PostMapping("/updateRuleConditionAction")
    @ApiOperation("保存或更新规则条件和动作")
    public AjaxResult updateRuleConditionAction(@RequestBody RuleConditionActionVo ruleConditionVo) {
        return AjaxResult.success(ruleConditionsService.updateRuleConditionAction(ruleConditionVo));
    }


}
