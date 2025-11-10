package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.UUIDUtil;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetFrameTaskDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetFrameTaskMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetFrameTaskService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_FRAME_TASK_NOT_EXISTS;

/**
 * 视频流帧捕获任务 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetFrameTaskServiceImpl implements DatasetFrameTaskService {

    @Resource
    private DatasetFrameTaskMapper frameTaskMapper;

    @Override
    public Long createDatasetFrameTask(DatasetFrameTaskSaveReqVO createReqVO) {
        // 插入
        DatasetFrameTaskDO frameTask = BeanUtils.toBean(createReqVO, DatasetFrameTaskDO.class);
        frameTask.setTaskCode(UUIDUtil.getUUID16());
        frameTaskMapper.insert(frameTask);
        // 返回
        return frameTask.getId();
    }

    @Override
    public void updateDatasetFrameTask(DatasetFrameTaskSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetFrameTaskExists(updateReqVO.getId());
        // 更新
        DatasetFrameTaskDO updateObj = BeanUtils.toBean(updateReqVO, DatasetFrameTaskDO.class);
        frameTaskMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetFrameTask(Long id) {
        // 校验存在
        validateDatasetFrameTaskExists(id);
        // 删除
        frameTaskMapper.deleteById(id);
    }

    private void validateDatasetFrameTaskExists(Long id) {
        if (frameTaskMapper.selectById(id) == null) {
            throw exception(DATASET_FRAME_TASK_NOT_EXISTS);
        }
    }

    @Override
    public DatasetFrameTaskDO getDatasetFrameTask(Long id) {
        return frameTaskMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetFrameTaskDO> getDatasetFrameTaskPage(DatasetFrameTaskPageReqVO pageReqVO) {
        return frameTaskMapper.selectPage(pageReqVO);
    }

}