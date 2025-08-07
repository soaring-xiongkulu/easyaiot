package com.basiclab.iot.device.service.rule_alarm;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.rule_alarm.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm.RuleAlarmDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 规则告警 Service 接口
 *
 * @author BasicLab
 */
public interface RuleAlarmService {

    /**
     * 创建规则告警
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createAlarm(@Valid RuleAlarmSaveReqVO createReqVO);

    /**
     * 更新规则告警
     *
     * @param updateReqVO 更新信息
     */
    void updateAlarm(@Valid RuleAlarmSaveReqVO updateReqVO);

    /**
     * 删除规则告警
     *
     * @param id 编号
     */
    void deleteAlarm(Long id);

    /**
     * 获得规则告警
     *
     * @param id 编号
     * @return 规则告警
     */
    RuleAlarmDO getAlarm(Long id);

    /**
     * 获得规则告警分页
     *
     * @param pageReqVO 分页查询
     * @return 规则告警分页
     */
    PageResult<RuleAlarmDO> getAlarmPage(RuleAlarmPageReqVO pageReqVO);

}