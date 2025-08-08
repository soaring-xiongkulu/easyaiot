package com.basiclab.iot.rule;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.rule.factory.RemoteRuleFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;

/**
 * @InterfaceDescription: 规则服务
 * @InterfaceName: RemoteRuleService
 * @Author: iot
 * @Date: 2021-12-31 10:57:16
 * @Version 1.0
 */

@FeignClient(contextId = "remoteRuleService", value = ServiceNameConstants.IOT_RULE, fallbackFactory = RemoteRuleFallbackFactory.class)
public interface RemoteRuleService {

    @GetMapping(value = "/ruleDeviceLinkage/triggerDeviceLinkage/{ruleIdentification}", headers = {"Authorization=Bearer 50684d1e14f54af5a36e74bf0bfb30aa"})
    public R<?> triggerDeviceLinkage(@PathVariable("ruleIdentification") String ruleIdentification);

    /**
     * 通过标识查询产品
     *
     * @param ruleIdentification
     * @return
     */
    @GetMapping("/ruleDeviceLinkage/actionCommandsByRuleIdentification/{ruleIdentification}")
    public R<?> actionCommandsByRuleIdentification(@PathVariable("ruleIdentification") String ruleIdentification);



    /**
     * 执行动作
     * @param ruleId
     * @return
     */
    @PostMapping("/ruleDeviceLinkage/executeRuleAction/{ruleId}")
    public AjaxResult executeRuleAction(@PathVariable("ruleId") String ruleId);


    /**
     * 检验规则
     * @param ruleId
     * @return
     */
    @PostMapping("/ruleDeviceLinkage/checkRuleConditions/{ruleId}")
    public AjaxResult checkRuleConditions(@PathVariable("ruleId") String ruleId);


}
