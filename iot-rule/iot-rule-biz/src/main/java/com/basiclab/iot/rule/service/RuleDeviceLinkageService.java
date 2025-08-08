package com.basiclab.iot.rule.service;

import com.basiclab.iot.common.domain.R;

/**
 * @program: basiclab
 * @description: 规则设备联动业务层接口
 * @packagename: com.mqttsnet.iot.rule.service
 * @Author: Basiclab
 * @e-mainl: 853017739@qq.com
 * @date: 2024-11-03 18:44
 **/
public interface RuleDeviceLinkageService {

    /**
     * 触发设备联动规则条件
     * @param ruleId 规则标识
     * @return
     */
    void triggerDeviceLinkageByRuleId(String ruleId);

    /**
     * 规则触发条件验证
     * @param ruleId 规则标识
     * @return
     */
    Boolean checkRuleConditions(String ruleId);
    /**
     * 获取所有产品
     * @return
     */
    R<?> selectAllProduct(String status);
    /**
     * 获取产品设备
     * @param productIdentification
     * @return
     */
    R<?> selectDeviceByProductIdentification(String productIdentification);


    /**
     * 获取产品服务
     * @param productIdentification
     * @return
     */
    R<?> selectProductServicesByProductIdentification(String productIdentification);


    /**
     * 根据产品id获取所有属性
     * @param serviceId
     * @return
     */
    R<?> selectProductPropertiesByServiceId(Long serviceId);

    /**
     * 根据产品id获取所有命令
     * @param serviceId
     * @return
     */
    R<?> selectProductCommandsByServiceId(Long serviceId);

    Boolean executeRuleAction(String ruleId);
}
