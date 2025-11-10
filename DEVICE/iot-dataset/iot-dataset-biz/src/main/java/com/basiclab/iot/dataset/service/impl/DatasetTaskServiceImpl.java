package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetTaskMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TASK_NOT_EXISTS;

/**
 * 标注任务 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetTaskServiceImpl implements DatasetTaskService {

    @Resource
    private DatasetTaskMapper taskMapper;

    @Override
    public Long createDatasetTask(DatasetTaskSaveReqVO createReqVO) {
        // 插入
        DatasetTaskDO task = BeanUtils.toBean(createReqVO, DatasetTaskDO.class);
        taskMapper.insert(task);
        // 返回
        return task.getId();
    }

    @Override
    public void updateDatasetTask(DatasetTaskSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetTaskExists(updateReqVO.getId());
        // 更新
        DatasetTaskDO updateObj = BeanUtils.toBean(updateReqVO, DatasetTaskDO.class);
        taskMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetTask(Long id) {
        // 校验存在
        validateDatasetTaskExists(id);
        // 删除
        taskMapper.deleteById(id);
    }

    private void validateDatasetTaskExists(Long id) {
        if (taskMapper.selectById(id) == null) {
            throw exception(DATASET_TASK_NOT_EXISTS);
        }
    }

    @Override
    public DatasetTaskDO getDatasetTask(Long id) {
        return taskMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetTaskDO> getDatasetTaskPage(DatasetTaskPageReqVO pageReqVO) {
        return taskMapper.selectPage(pageReqVO);
    }

}