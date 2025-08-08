package com.basiclab.iot.rule.service.impl;

import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.core.map.MapUtil;
import cn.hutool.extra.spring.SpringUtil;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONUtil;
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.JSONObject;
import com.alibaba.fastjson.TypeReference;
import com.basiclab.iot.broker.RemoteKafkaInfoApi;
import com.basiclab.iot.broker.domain.vo.KafkaMessageRequestVO;
import com.basiclab.iot.common.constant.Constants;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.mqs.ConsumerTopicConstant;
import com.basiclab.iot.common.utils.SpelComparisonUtil;
import com.basiclab.iot.device.constant.FunctionTypeConstant;
import com.basiclab.iot.device.constant.TdengineConstant;
import com.basiclab.iot.device.domain.device.vo.Device;
import com.basiclab.iot.rule.action.IAction;
import com.basiclab.iot.rule.action.factory.ActionFactory;
import com.basiclab.iot.rule.domain.RuleActionCommands;
import com.basiclab.iot.tdengine.RemoteTdEngineService;
import com.basiclab.iot.tdengine.domain.DeviceData;
import com.basiclab.iot.tdengine.domain.query.TDDeviceDataRequest;
import com.basiclab.iot.device.*;
import com.basiclab.iot.device.domain.device.vo.ProductProperties;
import com.basiclab.iot.rule.domain.RuleConditions;
import com.basiclab.iot.rule.domain.RuleLog;
import com.basiclab.iot.rule.domain.model.enums.RuleLogStatusEnum;
import com.basiclab.iot.rule.domain.model.vo.RuleConditionVo;
import com.basiclab.iot.rule.service.*;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * @program: basiclab
 * @description: 规则设备联动业务层接口实现类
 * @packagename: com.mqttsnet.iot.rule.service.impl
 * @Author: Basiclab
 * @e-mainl: 853017739@qq.com
 * @date: 2024-11-03 18:50
 **/
@Slf4j
@Service
public class RuleDeviceLinkageServiceImpl implements RuleDeviceLinkageService {


    @Resource
    private RemoteKafkaInfoApi remoteKafkaInfoApi;

    @Autowired
    private ActionCommandsService actionCommandsService;

    @Autowired
    private RuleConditionsService ruleConditionsService;

    @Resource
    private RemoteProductService remoteProductService;

    @Resource
    private RemoteTdEngineService remoteTdEngineService;

    @Resource
    private RemoteDeviceService remoteDeviceService;

    @Resource
    private RemoteProductServicesService remoteProductServicesService;

    @Resource
    private RemoteProductPropertiesService remoteProductPropertiesService;

    @Resource
    private RemoteProductCommandsService remoteProductCommandsService;

    @Resource
    private RuleLogService ruleLogService;


    /**
     * 单个设备下的所有属性的最新值   设备标识   属性code  属性最新值
     * 每个规则下都是唯一的一个对象 在单次执行完成规则后清空
     */
    private ConcurrentHashMap<String, Map<String, String>> newDataMap = new ConcurrentHashMap<>();

    /**
     * 逻辑分割符
     */
    private String logicSubStr = "@";


    /**
     * 触发设备联动规则条件
     *
     * @param ruleId 规则标识
     * @return
     */
    @Override
    @Transactional
    public void triggerDeviceLinkageByRuleId(String ruleId) {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("msg", ruleId);
        remoteKafkaInfoApi.sendMessage(KafkaMessageRequestVO.builder().topic(ConsumerTopicConstant.Rule.IOT_RULE_TRIGGER).message(jsonObject.toJSONString()).build());
    }

    /**
     * 规则触发条件验证
     *
     * @param ruleId 规则标识
     * @return
     */
    @Override
    public Boolean checkRuleConditions(String ruleId) {
        //执行时创建一个日志
        RuleLog ruleLog = generateRuleLog(Long.parseLong(ruleId), RuleLogStatusEnum.INITIAL.getCode());
        try {
            // 查询触发条件(目前情况下只有一个条件内容，json格式)
            RuleConditions ruleConditions = ruleConditionsService.getOneByRuleId(Long.parseLong(ruleId));
            Integer conditionType = ruleConditions.getConditionType();
            String conditionScheme = ruleConditions.getConditionScheme();
            //所有组条件结果  组的结果集合
            LinkedHashMap<String, Boolean> groupResultMap = new LinkedHashMap<>();
            String jsonString = JSON.parse(conditionScheme).toString();
            JSONArray objects = JSONUtil.parseArray(jsonString);
            List<RuleConditionVo> ruleConditionVoList = objects.toList(RuleConditionVo.class);
            int groupIndex = 1;
            for (int i = 0, ruleConditionVoListSize = ruleConditionVoList.size(); i < ruleConditionVoListSize; i++) {
                RuleConditionVo ruleConditionVo = ruleConditionVoList.get(i);
                String groupLogicalOperator = ruleConditionVo.getLogicalOperator();
                String groupLogicalOperatorStr = groupLogicalOperator + logicSubStr + groupIndex;
                groupIndex++;
                //单个子条件的与或关系  单个子条件结果
                LinkedHashMap<String, Boolean> childResultMap = new LinkedHashMap<>();
                //组内条件
                List<RuleConditionVo.ChildConditionVo> childConditionVos = ruleConditionVo.getConditions();
                int index = 1;
                for (RuleConditionVo.ChildConditionVo childCondition : childConditionVos) {
                    String logicalOperator = childCondition.getLogicalOperator();
                    String logicalOperatorStr = logicalOperator + logicSubStr + index;
                    index++;
                    RuleConditionVo.RightParam rightParam = childCondition.getRightParams();
                    String operatorStr = childCondition.getOperator().getValue();
                    RuleConditionVo.LeftParam leftParam = childCondition.getLeftParam();
                    Long propertyId = leftParam.getPropertyId();
                    String deviceIdentification = leftParam.getDeviceIdentification();
                    String productIdentification = leftParam.getProductIdentification();
                    R<ProductProperties> properties = remoteProductService.selectByIdProperties(propertyId);
                    ProductProperties propertiesData = properties.getData();
                    if (propertiesData == null) {
                        ruleLog.setLogAtTime(LocalDateTime.now());
                        ruleLog.setState(RuleLogStatusEnum.UNMATCHED_CONDITION.getCode());
                        ruleLog.setContent("check condition failed, Failed to query productProperties info");
                        updateRuleLog(ruleLog);
                        continue;
                    }
                    // 属性Code
                    String propertyCode = propertiesData.getPropertyCode();
                    //单个条件下所有设备匹配结果
                    List<Boolean> allDiviceResult = new ArrayList<>();
                    if ("ALL".equals(deviceIdentification)) {
                        //匹配所有设备
                        AjaxResult ajaxResult = remoteDeviceService.selectByProductIdentification(productIdentification);
                        List<Device> deviceList = (List<Device>) ajaxResult.get("data");
                        if (CollectionUtils.isEmpty(deviceList)) {
                            ruleLog.setLogAtTime(LocalDateTime.now());
                            ruleLog.setState(RuleLogStatusEnum.UNMATCHED_CONDITION.getCode());
                            ruleLog.setContent("check condition failed, Failed to query device info");
                            updateRuleLog(ruleLog);
                            break;
                        }
                        for (Device device : deviceList) {
                            String singleDeviceIdentification = device.getDeviceIdentification();
                            handleCompareResult(singleDeviceIdentification, propertyCode, operatorStr, rightParam, allDiviceResult, ruleLog);
                        }
                    } else {
                        //单个设备
                        handleCompareResult(deviceIdentification, propertyCode, operatorStr, rightParam, allDiviceResult, ruleLog);
                    }
                    //单条件结果 设备下结果必须满足
                    Boolean singleResult = handleDeviceResult(allDiviceResult);
                    childResultMap.put(logicalOperatorStr, singleResult);
                }
                //处理子条件集合与或关系  即单个组的结果
                boolean groupResult = handleLogicMap(childResultMap);
                groupResultMap.put(groupLogicalOperatorStr, groupResult);
            }
            boolean result = handleLogicMap(groupResultMap);
            if (result) {
                ruleLog.setLogAtTime(LocalDateTime.now());
                ruleLog.setState(RuleLogStatusEnum.MATCHED_CONDITION.getCode());
                ruleLog.setContent("condition is  successful checked");
                updateRuleLog(ruleLog);
            }
            return result;
        } catch (NumberFormatException e) {
            ruleLog.setLogAtTime(LocalDateTime.now());
            ruleLog.setContent(e.toString());
            ruleLog.setSuccess(0);
            ruleLog.setState(RuleLogStatusEnum.UNMATCHED_CONDITION.getCode());
            updateRuleLog(ruleLog);
            throw new RuntimeException(e);
        }
    }


    /**
     * 生成规则日志
     *
     * @param ruleId    规则id
     * @param logStatus 日志状态
     */
    private RuleLog generateRuleLog(Long ruleId, String logStatus) {
        RuleLog ruleLog = RuleLog.builder()
                .ruleId(ruleId)
                .state(logStatus)
                .content("ready to start validating the rule")
                .success(0)
                .logAtTime(LocalDateTime.now())
                .createTime(LocalDateTime.now())
                .updateTime(LocalDateTime.now())
                .createBy("system")
                .updateBy("system")
                .build();
        //每个规则执行日志只保存最新10条执行记录
        List<RuleLog> ruleLogs = ruleLogService.selectListByRuleId(ruleId);
        if (ruleLogs.size() > 10) {
            List<RuleLog> removeList = ruleLogs.stream().skip(10).collect(Collectors.toList());
            ruleLogService.removeBatchByIds(removeList);
        }
        ruleLogService.save(ruleLog);
        return ruleLog;
    }


    /**
     * 更新规则日志
     *
     * @param ruleLog 规则日志
     */
    private RuleLog updateRuleLog(RuleLog ruleLog) {
        ruleLogService.updateById(ruleLog);
        return ruleLog;
    }


    /**
     * 处理条件集合的与或逻辑关系
     *
     * @param childResultMap
     * @return
     */
    private boolean handleLogicMap(LinkedHashMap<String, Boolean> childResultMap) {
        int index = 1;
        Boolean last = true;
        boolean result = false;
        for (Map.Entry<String, Boolean> booleanEntry : childResultMap.entrySet()) {
            String logicStr = booleanEntry.getKey();
            String[] split = logicStr.split(logicSubStr);
            String logic = split[0];
            Boolean childResult = booleanEntry.getValue();
            result = SpelComparisonUtil.compare(last, logic, childResult);
            last = childResult;
            index++;
        }
        return result;
    }


    /**
     * 处理设备结果
     *
     * @param allConditionResult
     * @return
     */
    private static Boolean handleDeviceResult(List<Boolean> allConditionResult) {
        return allConditionResult.stream().allMatch(s -> s.equals(true));
    }

    /**
     * 处理对比结果 将对比结果放入list中
     *
     * @param singleDeviceIdentification 设备唯一标识
     * @param propertyCode               属性编码
     * @param operatorStr                比较符号
     * @param rightParam                 被比较属性值
     * @param allDiviceResult            所有设备结果
     * @param ruleLog                    规则日志    执行细节出增加日志方便定位问题
     */
    private void handleCompareResult(String singleDeviceIdentification, String propertyCode, String operatorStr, RuleConditionVo.RightParam rightParam, List<Boolean> allDiviceResult, RuleLog ruleLog) {
        R<List<DeviceData>> deviceDataListR = getListR(singleDeviceIdentification, propertyCode);
        List<DeviceData> deviceDataList = null;
        if (deviceDataListR != null && deviceDataListR.getData() != null) {
            deviceDataList = deviceDataListR.getData();
        }
        if (!CollectionUtils.isEmpty(deviceDataList)) {
            deviceDataList.sort(Comparator.comparing(DeviceData::getLastUpdateTime, Comparator.nullsFirst(Comparator.naturalOrder())).reversed());
            DeviceData deviceData = deviceDataList.get(0);
            HashMap<String, String> propertyMap = MapUtil.newHashMap();
            propertyMap.put(propertyCode, deviceData.getDataValue());
            newDataMap.put(singleDeviceIdentification, propertyMap);
            String dataValue = deviceData.getDataValue();
            boolean compare = SpelComparisonUtil.compare(dataValue, operatorStr, rightParam.getValue());
            allDiviceResult.add(compare);
        } else {
            //此处若  若远程调用失败返回空默认失败
            log.error("查询Tdengine中属性数据失败,导致匹配结果失败 : " + JSONObject.toJSONString(deviceDataListR));
            ruleLog.setLogAtTime(LocalDateTime.now());
            ruleLog.setState(RuleLogStatusEnum.UNMATCHED_CONDITION.getCode());
            ruleLog.setContent("check condition failed, Failed to query attribute data in Tdengine");
            updateRuleLog(ruleLog);
            allDiviceResult.add(false);
        }
    }

    /**
     * TD查询设备属性
     *
     * @param singleDeviceIdentification 设备id
     * @param propertyCode               属性编码
     * @return
     */
    private R<List<DeviceData>> getListR(String singleDeviceIdentification, String propertyCode) {
        TDDeviceDataRequest request = new TDDeviceDataRequest();
        request.setDeviceIdentification(singleDeviceIdentification);
        List<String> propertyCodeList = CollectionUtil.newArrayList(propertyCode);
        request.setIdentifierList(propertyCodeList);
        request.setFunctionType(FunctionTypeConstant.PROPERTIES);
        request.setTdDatabaseName(TdengineConstant.IOT_DEVICE);
        request.setTdSuperTableName(TdengineConstant.DEVICE_DATA);
        R<List<DeviceData>> deviceDataListR = remoteTdEngineService.getLastRowsListByIdentifier(request);
        return deviceDataListR;
    }


    /**
     * 获取所有可用产品
     *
     * @return
     */
    public R<?> selectAllProduct(String status) {
        R<?> productResponse = remoteProductService.selectAllProduct(status);
        return productResponse;
    }

    /**
     * 根据产品标识获取产品所有设备
     *
     * @param productIdentification
     * @return
     */
    public R<?> selectDeviceByProductIdentification(String productIdentification) {
        R<?> deviceResponse = remoteDeviceService.selectAllByProductIdentification(productIdentification);
        return deviceResponse;
    }


    /**
     * 根据产品标识获取产品所有服务
     *
     * @param productIdentification
     * @return
     */
    public R<?> selectProductServicesByProductIdentification(String productIdentification) {
        R<?> productServicesResponse = remoteProductServicesService.selectAllByProductIdentificationAndStatus(productIdentification, Constants.ENABLE);
        return productServicesResponse;
    }

    /**
     * 根据服务id获取服务所有属性
     *
     * @param serviceId
     * @return
     */
    public R<?> selectProductPropertiesByServiceId(Long serviceId) {
        R<?> propertiesResponse = remoteProductPropertiesService.selectAllByServiceId(serviceId);
        return propertiesResponse;
    }

    /**
     * 根据服务id获取服务所有命令
     *
     * @param serviceId
     * @return
     */
    public R<?> selectProductCommandsByServiceId(Long serviceId) {
        R<?> propertiesResponse = remoteProductCommandsService.selectAllByServiceId(serviceId);
        return propertiesResponse;
    }

    /**
     * 执行规则动作
     *
     * @param ruleId
     */
    @Override
    public Boolean executeRuleAction(String ruleId) {
        //更新执行动作日志
        RuleLog ruleLog = ruleLogService.getByRuleId(ruleId);
        ruleLog.setState(RuleLogStatusEnum.EXECUTING_ACTION.getCode());
        ruleLog.setLogAtTime(LocalDateTime.now());
        updateRuleLog(ruleLog);

        try {
            List<RuleActionCommands> ruleActionCommands = actionCommandsService.actionCommandsByRuleId(ruleId);
            for (RuleActionCommands actionCommand : ruleActionCommands) {
                String actionType = actionCommand.getActionType();
                ActionFactory actionFactory = SpringUtil.getBean(ActionFactory.class);
                IAction action = actionFactory.getActionByType(actionType);
                action.execute(actionCommand, newDataMap);
            }
            //执行完成将map中的数据清除
            clearData(ruleId);
            ruleLog.setLogAtTime(LocalDateTime.now());
            ruleLog.setContent("the action is executed successfully");
            ruleLog.setSuccess(1);
            ruleLog.setState(RuleLogStatusEnum.EXECUTED_ACTION.getCode());
            updateRuleLog(ruleLog);
        } catch (Exception e) {
            ruleLog.setLogAtTime(LocalDateTime.now());
            ruleLog.setContent("The rule execution failed:" + e.toString());
            ruleLog.setSuccess(0);
            ruleLog.setState(RuleLogStatusEnum.EXECUTED_FAIL.getCode());
            updateRuleLog(ruleLog);
            throw new RuntimeException(e);
        }
        return true;
    }

    /**
     * 动作执行完成清除map中的数据
     *
     * @param ruleId
     */
    private void clearData(String ruleId) {
        RuleConditions ruleConditions = ruleConditionsService.getOneByRuleId(Long.parseLong(ruleId));
        String conditionScheme = ruleConditions.getConditionScheme();
        List<RuleConditionVo> ruleConditionVoList = JSON.parseObject(conditionScheme, new TypeReference<List<RuleConditionVo>>() {
        });

        for (RuleConditionVo ruleConditionVo : ruleConditionVoList) {

            List<RuleConditionVo.ChildConditionVo> childConditionVos = ruleConditionVo.getConditions();
            for (RuleConditionVo.ChildConditionVo childCondition : childConditionVos) {
                RuleConditionVo.LeftParam leftParam = childCondition.getLeftParam();
                String deviceIdentification = leftParam.getDeviceIdentification();
                String productIdentification = leftParam.getProductIdentification();
                //单个条件下所有设备匹配结果
                if ("ALL".equals(deviceIdentification)) {
                    //匹配所有设备
                    AjaxResult ajaxResult = remoteDeviceService.selectByProductIdentification(productIdentification);
                    List<Device> deviceList = (List<Device>) ajaxResult.get("data");
                    if (CollectionUtils.isEmpty(deviceList)) {
                        break;
                    }
                    for (Device device : deviceList) {
                        String singleDeviceIdentification = device.getDeviceIdentification();
                        newDataMap.remove(singleDeviceIdentification);
                    }
                } else {
                    //单个设备
                    newDataMap.remove(deviceIdentification);
                }

            }
        }
    }
}
