package com.basiclab.iot.rule.controller;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.rule.service.RuleDeviceLinkageService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

/**
 * @program: EasyAIoT
 * @description: 设备联动Controller
 * @packagename: com.mqttsnet.iot.rule.controller
 * @author EasyAIoT
 * @date: 2025-08-07 20:31
 **/
@RestController
@RequestMapping("/ruleDeviceLinkage")
@Slf4j
@Tag(name  = "设备联动管理")
public class RuleDeviceLinkageController extends BaseController {


    @Autowired
    private RuleDeviceLinkageService ruleDeviceLinkageService;

    /**
     * 触发设备联动规则条件
     * @param ruleId 规则标识
     * @return
     */
    @GetMapping(value = "/triggerDeviceLinkage/{ruleId}")
    @ApiOperation("触发设备联动规则条件")
    public R<?> triggerDeviceLinkage(@PathVariable("ruleId") String ruleId) {
        ruleDeviceLinkageService.triggerDeviceLinkageByRuleId(ruleId);
        return R.ok();
    }

    /**
     * 获取所有的产品
     * @return
     */
    @GetMapping("/selectAllProduct")
    @ApiOperation("获取所有的产品")
    public R<?> selectAllProduct(){
        return ruleDeviceLinkageService.selectAllProduct("0");
    }


    /**
     * 根据产品标识获取产品关联设备
     * @param productIdentification
     * @return
     */
    @GetMapping("/selectDeviceByProductIdentification/{productIdentification}")
    @ApiOperation("根据产品标识获取产品关联设备")
    public R<?> selectDeviceByProductIdentification(@PathVariable("productIdentification") String productIdentification){
        return ruleDeviceLinkageService.selectDeviceByProductIdentification(productIdentification);
    }


    /**
     * 根据产品标识获取产品关联服务
     * @param productIdentification
     * @return
     */
    @ApiOperation("根据产品标识获取产品关联设备")
    @GetMapping("/selectProductServicesByProductIdentification/{productIdentification}")
    public R<?> selectProductServicesByProductIdentification(@PathVariable("productIdentification") String productIdentification){
        return ruleDeviceLinkageService.selectProductServicesByProductIdentification(productIdentification);
    }

    @ApiOperation("通过服务id获取产品属性")
    @GetMapping("/selectProductPropertiesByServiceId/{serviceId}")
    public R<?> selectProductPropertiesByServiceId(@PathVariable("serviceId") Long serviceId){
        return ruleDeviceLinkageService.selectProductPropertiesByServiceId(serviceId);
    }

    @ApiOperation("通过服务id获取命令")
    @GetMapping("/selectProductCommandsByServiceId/{serviceId}")
    public R<?> selectProductCommandsByServiceId(@PathVariable("serviceId") Long serviceId){
        return ruleDeviceLinkageService.selectProductCommandsByServiceId(serviceId);
    }

    /**
     *
     * @param ruleId
     * @return
     */
    @ApiOperation("校验规则条件")
    @PostMapping("/checkRuleConditions/{ruleId}")
    public AjaxResult checkRuleConditions(@PathVariable("ruleId") String ruleId){
        return AjaxResult.success(ruleDeviceLinkageService.checkRuleConditions(ruleId));
    }


    /**
     *
     * @param ruleId
     * @return
     */
    @ApiOperation("执行规则动作")
    @PostMapping("/executeRuleAction/{ruleId}")
    public AjaxResult executeRuleAction(@PathVariable("ruleId") String ruleId){
        return AjaxResult.success(ruleDeviceLinkageService.executeRuleAction(ruleId));
    }
}
