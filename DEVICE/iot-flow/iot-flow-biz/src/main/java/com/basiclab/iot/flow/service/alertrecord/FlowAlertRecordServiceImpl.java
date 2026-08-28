package com.basiclab.iot.flow.service.alertrecord;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.exception.util.ServiceExceptionUtil;
import com.basiclab.iot.flow.controller.admin.task.FlowTaskVOs;
import com.basiclab.iot.flow.dal.dataobject.FlowAlertRecordDO;
import com.basiclab.iot.flow.dal.pgsql.FlowAlertRecordMapper;
import com.basiclab.iot.flow.service.alert.FlowAlertProcessService;
import com.basiclab.iot.flow.service.task.FlowTaskService;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static com.basiclab.iot.flow.enums.FlowErrorCodeConstants.ALERT_RECORD_NOT_EXISTS;

/**
 * 告警处理记录 Service 实现类
 */
@Service
public class FlowAlertRecordServiceImpl implements FlowAlertRecordService {

    @Resource
    private FlowAlertRecordMapper alertRecordMapper;
    @Resource
    private FlowAlertProcessService alertProcessService;
    @Resource
    private FlowTaskService taskService;

    @Override
    public PageResult<FlowAlertRecordDO> getAlertRecordPage(PageParam pageParam, Long alertId, String alertSource,
                                                            Integer processInstanceStatus) {
        return alertRecordMapper.selectPage(pageParam, alertId, alertSource, processInstanceStatus);
    }

    @Override
    public PageResult<FlowAlertRecordDO> getMyAlertRecordPage(Long userId, PageParam pageParam, Long alertId,
                                                              String alertSource, Integer processInstanceStatus) {
        // 我负责 = 我名下有运行中任务（assignee/candidate）的实例
        PageResult<FlowTaskVOs.TaskVO> todoPage = taskService.getTaskTodoPage(userId, buildNoPageParam(), null, null);
        if (todoPage.getList().isEmpty()) {
            return PageResult.empty();
        }
        Set<String> instanceIds = todoPage.getList().stream()
                .map(FlowTaskVOs.TaskVO::getProcessInstanceId).collect(Collectors.toSet());
        PageResult<FlowAlertRecordDO> page = alertRecordMapper.selectPage(pageParam, alertId, alertSource,
                processInstanceStatus);
        List<FlowAlertRecordDO> mine = page.getList().stream()
                .filter(record -> instanceIds.contains(record.getProcessInstanceId()))
                .collect(Collectors.toList());
        return new PageResult<>(mine, (long) mine.size());
    }

    private PageParam buildNoPageParam() {
        PageParam pageParam = new PageParam();
        pageParam.setPageNo(1);
        pageParam.setPageSize(PageParam.PAGE_SIZE_NONE);
        return pageParam;
    }

    @Override
    public List<FlowAlertRecordDO> getAlertRecordListByAlertIds(Collection<Long> alertIds) {
        if (alertIds == null || alertIds.isEmpty()) {
            return new ArrayList<>();
        }
        return alertRecordMapper.selectListByAlertIds(alertIds);
    }

    @Override
    public FlowAlertRecordDO getAlertRecord(Long id) {
        FlowAlertRecordDO record = alertRecordMapper.selectById(id);
        if (record == null) {
            throw ServiceExceptionUtil.exception(ALERT_RECORD_NOT_EXISTS);
        }
        return record;
    }

    @Override
    public FlowAlertRecordDO triggerAlertRecord(Long alertId, String processDefinitionKey) {
        return alertProcessService.manualTrigger(alertId, processDefinitionKey);
    }

}
