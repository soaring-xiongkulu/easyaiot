package com.basiclab.iot.rule.controller;

import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;


import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.rule.service.ActionCommandsService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;

@Tag(name  = "规则动作管理")
@RequestMapping("/actionCommands")
@RestController
public class ActionCommandsController extends BaseController {


    @Resource
    private ActionCommandsService actionCommandsService;

    /**
     * 通过规则id查询规则动作
     *
     * @param ruleId 规则id
     * @return 单条数据
     */
    @GetMapping("/actionCommandsByRuleIdentification/{ruleId}")
    @ApiOperation("通过规则id查询规则动作")
    public R<?> actionCommandsByRuleIdentification(@PathVariable(value = "ruleId") String ruleId) {
        return R.ok(actionCommandsService.actionCommandsByRuleId(ruleId));
    }


    //    //@PreAuthorize(hasPermi = "rule:rule:list")
    @GetMapping("/list")
    @ApiOperation("规则动作列表")
    public TableDataInfo list(RuleActionCommands ruleActionCommands) {
        startPage();
        List<RuleActionCommands> list = actionCommandsService.selectByActionCommandsSelective(ruleActionCommands);
        return getDataTable(list);
    }

    /**
     * 批量新增执行动作命令
     */
    @NoRepeatSubmit
//    //@PreAuthorize(hasPermi = "rule:actionCommands:add")
    ////@Log(title = "执行动作命令", businessType = BusinessType.INSERT)
    @PostMapping("/batchInsert")
    @ApiOperation("批量新增执行动作命令")
    public AjaxResult batchInsert(@RequestBody List<RuleActionCommands> ruleActionCommandsList) {
        return AjaxResult.success(actionCommandsService.batchInsert(ruleActionCommandsList));
    }

    /**
     * 批量编辑执行动作命令
     */
    @NoRepeatSubmit
//    //@PreAuthorize(hasPermi = "rule:actionCommands:edit")
    ////@Log(title = "执行动作命令", businessType = BusinessType.UPDATE)
    @PutMapping("/batchEdit")
    @ApiOperation("批量编辑执行动作命令")
    public AjaxResult updateBatch(@RequestBody List<RuleActionCommands> ruleActionCommandsList) {
        return toAjax(actionCommandsService.updateBatchSelective(ruleActionCommandsList));
    }

    /**
     * 批量删除执行动作命令
     *
     * @param ids
     * @return
     */
//    //@PreAuthorize(hasPermi = "link:actionCommands:remove")
    ////@Log(title = "执行动作命令", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    @ApiOperation("批量删除执行动作命令")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(actionCommandsService.deleteBatchByIds(ids));
    }
}
