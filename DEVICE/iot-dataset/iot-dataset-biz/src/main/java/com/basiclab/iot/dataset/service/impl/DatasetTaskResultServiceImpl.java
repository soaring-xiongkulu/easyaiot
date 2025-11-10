package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskResultDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetTaskResultMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskResultService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TASK_RESULT_NOT_EXISTS;


/**
 * 标注任务结果 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetTaskResultServiceImpl implements DatasetTaskResultService {

    @Resource
    private DatasetTaskResultMapper taskResultMapper;

    @Override
    public Long createDatasetTaskResult(DatasetTaskResultSaveReqVO createReqVO) {
        // 插入
        DatasetTaskResultDO taskResult = BeanUtils.toBean(createReqVO, DatasetTaskResultDO.class);
        taskResultMapper.insert(taskResult);
        // 返回
        return taskResult.getId();
    }

    @Override
    public void updateDatasetTaskResult(DatasetTaskResultSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetTaskResultExists(updateReqVO.getId());
        // 更新
        DatasetTaskResultDO updateObj = BeanUtils.toBean(updateReqVO, DatasetTaskResultDO.class);
        taskResultMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetTaskResult(Long id) {
        // 校验存在
        validateDatasetTaskResultExists(id);
        // 删除
        taskResultMapper.deleteById(id);
    }

    private void validateDatasetTaskResultExists(Long id) {
        if (taskResultMapper.selectById(id) == null) {
            throw exception(DATASET_TASK_RESULT_NOT_EXISTS);
        }
    }

    @Override
    public DatasetTaskResultDO getDatasetTaskResult(Long id) {
        return taskResultMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetTaskResultDO> getDatasetTaskResultPage(DatasetTaskResultPageReqVO pageReqVO) {
        return taskResultMapper.selectPage(pageReqVO);
    }

}