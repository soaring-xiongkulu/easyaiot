package com.basiclab.iot.device.service.ota_tasks;

import com.basiclab.iot.device.dal.mysql.ota_tasks.OtaTasksMapper;
import org.springframework.stereotype.Service;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;

import com.basiclab.iot.device.controller.admin.ota_tasks.vo.*;
import com.basiclab.iot.device.dal.dataobject.ota_tasks.OtaTasksDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;

import static com.basiclab.iot.device.enums.ErrorCodeConstants.OTA_TASKS_NOT_EXISTS;
import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;

/**
 * OTA升级任务 Service 实现类
 *
 * @author BasicLab
 */
@Service
@Validated
public class OtaTasksServiceImpl implements OtaTasksService {

    @Resource
    private OtaTasksMapper tasksMapper;

    @Override
    public Long createTasks(OtaTasksSaveReqVO createReqVO) {
        // 插入
        OtaTasksDO tasks = BeanUtils.toBean(createReqVO, OtaTasksDO.class);
        tasksMapper.insert(tasks);
        // 返回
        return tasks.getId();
    }

    @Override
    public void updateTasks(OtaTasksSaveReqVO updateReqVO) {
        // 校验存在
        validateTasksExists(updateReqVO.getId());
        // 更新
        OtaTasksDO updateObj = BeanUtils.toBean(updateReqVO, OtaTasksDO.class);
        tasksMapper.updateById(updateObj);
    }

    @Override
    public void deleteTasks(Long id) {
        // 校验存在
        validateTasksExists(id);
        // 删除
        tasksMapper.deleteById(id);
    }

    private void validateTasksExists(Long id) {
        if (tasksMapper.selectById(id) == null) {
            throw exception(OTA_TASKS_NOT_EXISTS);
        }
    }

    @Override
    public OtaTasksDO getTasks(Long id) {
        return tasksMapper.selectById(id);
    }

    @Override
    public PageResult<OtaTasksDO> getTasksPage(OtaTasksPageReqVO pageReqVO) {
        return tasksMapper.selectPage(pageReqVO);
    }

}