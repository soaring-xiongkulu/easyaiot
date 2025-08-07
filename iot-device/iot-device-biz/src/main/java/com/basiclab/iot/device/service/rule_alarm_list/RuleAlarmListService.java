package com.basiclab.iot.device.service.rule_alarm_list;

import javax.validation.*;
import com.basiclab.iot.device.controller.admin.rule_alarm_list.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm_list.RuleAlarmListDO;
import com.basiclab.iot.common.domain.PageResult;

/**
 * 告警列 Service 接口
 *
 * @author BasicLab
 */
public interface RuleAlarmListService {

    /**
     * 创建告警列
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createAlarmList(@Valid RuleAlarmListSaveReqVO createReqVO);

    /**
     * 更新告警列
     *
     * @param updateReqVO 更新信息
     */
    void updateAlarmList(@Valid RuleAlarmListSaveReqVO updateReqVO);

    /**
     * 删除告警列
     *
     * @param id 编号
     */
    void deleteAlarmList(Long id);

    /**
     * 获得告警列
     *
     * @param id 编号
     * @return 告警列
     */
    RuleAlarmListDO getAlarmList(Long id);

    /**
     * 获得告警列分页
     *
     * @param pageReqVO 分页查询
     * @return 告警列分页
     */
    PageResult<RuleAlarmListDO> getAlarmListPage(RuleAlarmListPageReqVO pageReqVO);

}