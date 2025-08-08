package com.basiclab.iot.rule.controller;

import com.alibaba.fastjson.JSONObject;
import com.basiclab.iot.common.annotation.NoRepeatSubmit;
import com.basiclab.iot.common.annotations.PreAuthorize;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.exception.job.TaskException;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.job.RemoteJobService;
import com.basiclab.iot.job.domain.SysJob;
import com.basiclab.iot.rule.domain.Rule;
import com.basiclab.iot.rule.domain.model.RuleModel;
import com.basiclab.iot.rule.service.ActionCommandsService;
import com.basiclab.iot.rule.service.RuleConditionsService;
import com.basiclab.iot.rule.service.RuleService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.quartz.SchedulerException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.LinkedHashMap;
import java.util.List;


/**
 * 规则处理类
 *
 * @author shisen
 */
@Tag(name  = "规则管理")
@RestController
@RequestMapping("/rule")
public class RuleController extends BaseController {

    @Autowired
    private RuleService ruleService;

    @Autowired
    private RuleConditionsService ruleConditionsService;

    @Resource
    private ActionCommandsService actionCommandsService;

    @Resource
    private RemoteJobService remoteJobService;


    /**
     * 查询规则管理列表
     */
    @ApiOperation("查询规则管理列表")
    // @PreAuthorize(hasPermi = "rule:rule:list")
    @GetMapping("/list")
    public TableDataInfo list(Rule rule) {
        startPage();
        List<Rule> list = ruleService.selectRuleList(rule);
        return getDataTable(list);
    }


    /**
     * 获取规则详细信息
     */
    // @PreAuthorize(hasPermi = "rule:rule:query")
    @ApiOperation("获取规则详细信息")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(ruleService.selectByPrimaryKey(id));
    }

    /**
     * 获取规则详细信息
     */
    // @PreAuthorize(hasPermi = "rule:rule:query")
    @ApiOperation("获取规则详细信息")
    @GetMapping(value = "/getFullInfo/{id}")
    public AjaxResult getFullInfo(@PathVariable("id") Long id) {
        RuleModel ruleModel = ruleService.selectFullRuleById(id);
        return AjaxResult.success(ruleModel);
    }

    /**
     * 新增规则
     */
    @NoRepeatSubmit
    // @PreAuthorize(hasPermi = "rule:rule:add")
    //@Log(title = "新增规则", businessType = BusinessType.INSERT)
    @PostMapping
    @ApiOperation("新增规则")
    public AjaxResult add(@RequestBody Rule rule) {
        return AjaxResult.success(ruleService.insert(rule));
    }

    /**
     * 修改规则
     */
    @NoRepeatSubmit
//    // @PreAuthorize(hasPermi = "rule:rule:edit")
    //@Log(title = "规则管理", businessType = BusinessType.UPDATE)
    @PutMapping
    @ApiOperation("修改规则")
    public AjaxResult edit(@RequestBody Rule rule) {
        boolean b = ruleService.updateById(rule);
        if (b) {
            //同步更新job任务状态
            Rule rule1 = ruleService.getById(rule.getId());
            String jobIdentification = rule1.getJobIdentification();
            String status = rule1.getStatus();
            AjaxResult ajaxResult = remoteJobService.getInfo(Long.parseLong(jobIdentification));
            LinkedHashMap data = (LinkedHashMap) ajaxResult.get("data");
            SysJob sysJob = JSONObject.parseObject(JSONObject.toJSONString(data), SysJob.class);
            sysJob.setStatus(status);
            sysJob.setCronExpression(rule1.getCronExpression());
            sysJob.setMisfirePolicy(rule1.getMisfirePolicy());
            sysJob.setConcurrent(rule1.getConcurrent());
            try {
                AjaxResult edit = remoteJobService.edit(sysJob);
            } catch (SchedulerException | TaskException e) {
                throw new RuntimeException(e);
            }
        }
        return toAjax(b);
    }

    /**
     * 删除规则管理
     */
//    // @PreAuthorize(hasPermi = "rule:rule:remove")
    //@Log(title = "规则删除", businessType = BusinessType.DELETE)
    @DeleteMapping("/{id}")
    @ApiOperation("删除规则管理")
    public AjaxResult remove(@PathVariable Long id) {
        //同步删除job任务
        Rule rule = ruleService.getById(id);
        try {
            remoteJobService.remove(new Long[]{Long.parseLong(rule.getJobIdentification())});
        } catch (SchedulerException | TaskException e) {
            throw new RuntimeException(e);
        }
        boolean result = ruleService.removeById(id);
        if (result) {
            //将对应的规则条件和规则动作删除
            ruleConditionsService.removeByRuleId(id);
            actionCommandsService.removeByRuleId(id);
        }

        return toAjax(result);
    }


    /**
     * 修改场景联动状态
     */
    @ApiOperation("修改场景联动状态")
    //@Log(title = "场景联动", businessType = BusinessType.UPDATE)
    @PutMapping("/updateStatus")
    public AjaxResult updateStatus(@RequestBody Rule rule) {

        boolean b = ruleService.updateById(rule);
        if (b) {
            Rule ruleInfo = ruleService.getById(rule.getId());
            String status = rule.getStatus();

            try {
                SysJob sysJob = new SysJob();
                sysJob.setJobId(Long.parseLong(ruleInfo.getJobIdentification()));
                sysJob.setStatus(status);
                remoteJobService.changeStatus(sysJob);
            } catch (SchedulerException e) {
                throw new RuntimeException(e);
            }
        }
        return toAjax(b);
    }

}
