package com.basiclab.iot.device.service.rule_alarm_list;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.rule_alarm_list.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm_list.RuleAlarmListDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.rule_alarm_list.AlarmListMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.RULE_ALARM_LIST_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 告警列 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class RuleAlarmListServiceImpl implements RuleAlarmListService {

    @Resource
    private AlarmListMapper alarmListMapper;

    @Override
    public Long createAlarmList(RuleAlarmListSaveReqVO createReqVO) {
        // 插入
        RuleAlarmListDO alarmList = BeanUtils.toBean(createReqVO, RuleAlarmListDO.class);
        alarmListMapper.insert(alarmList);
        // 返回
        return alarmList.getId();
    }

    @Override
    public void updateAlarmList(RuleAlarmListSaveReqVO updateReqVO) {
        // 校验存在
        validateAlarmListExists(updateReqVO.getId());
        // 更新
        RuleAlarmListDO updateObj = BeanUtils.toBean(updateReqVO, RuleAlarmListDO.class);
        alarmListMapper.updateById(updateObj);
    }

    @Override
    public void deleteAlarmList(Long id) {
        // 校验存在
        validateAlarmListExists(id);
        // 删除
        alarmListMapper.deleteById(id);
    }

    private void validateAlarmListExists(Long id) {
        if (alarmListMapper.selectById(id) == null) {
            throw exception(RULE_ALARM_LIST_NOT_EXISTS);
        }
    }

    @Override
    public RuleAlarmListDO getAlarmList(Long id) {
        return alarmListMapper.selectById(id);
    }

    @Override
    public PageResult<RuleAlarmListDO> getAlarmListPage(RuleAlarmListPageReqVO pageReqVO) {
        return alarmListMapper.selectPage(pageReqVO);
    }

}