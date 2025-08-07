package com.basiclab.iot.device.service.rule_alarm;

import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.rule_alarm.vo.*;
import com.basiclab.iot.device.dal.dataobject.rule_alarm.RuleAlarmDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import com.basiclab.iot.device.dal.mysql.rule_alarm.RuleAlarmMapper;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.RULE_ALARM_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * 规则告警 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class RuleAlarmServiceImpl implements RuleAlarmService {

    @Resource
    private RuleAlarmMapper alarmMapper;

    @Override
    public Long createAlarm(RuleAlarmSaveReqVO createReqVO) {
        // 插入
        RuleAlarmDO alarm = BeanUtils.toBean(createReqVO, RuleAlarmDO.class);
        alarmMapper.insert(alarm);
        // 返回
        return alarm.getId();
    }

    @Override
    public void updateAlarm(RuleAlarmSaveReqVO updateReqVO) {
        // 校验存在
        validateAlarmExists(updateReqVO.getId());
        // 更新
        RuleAlarmDO updateObj = BeanUtils.toBean(updateReqVO, RuleAlarmDO.class);
        alarmMapper.updateById(updateObj);
    }

    @Override
    public void deleteAlarm(Long id) {
        // 校验存在
        validateAlarmExists(id);
        // 删除
        alarmMapper.deleteById(id);
    }

    private void validateAlarmExists(Long id) {
        if (alarmMapper.selectById(id) == null) {
            throw exception(RULE_ALARM_NOT_EXISTS);
        }
    }

    @Override
    public RuleAlarmDO getAlarm(Long id) {
        return alarmMapper.selectById(id);
    }

    @Override
    public PageResult<RuleAlarmDO> getAlarmPage(RuleAlarmPageReqVO pageReqVO) {
        return alarmMapper.selectPage(pageReqVO);
    }

}