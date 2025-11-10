package com.basiclab.iot.dataset.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskUserDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetTaskUserMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskUserSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTaskUserService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TASK_USER_NOT_EXISTS;

/**
 * 标注任务用户 Service 实现类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
@Validated
public class DatasetTaskUserServiceImpl implements DatasetTaskUserService {

    @Resource
    private DatasetTaskUserMapper taskUserMapper;

    @Override
    public Long createDatasetTaskUser(DatasetTaskUserSaveReqVO createReqVO) {
        // 插入
        DatasetTaskUserDO taskUser = BeanUtils.toBean(createReqVO, DatasetTaskUserDO.class);
        taskUserMapper.insert(taskUser);
        // 返回
        return taskUser.getId();
    }

    @Override
    public void updateDatasetTaskUser(DatasetTaskUserSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetTaskUserExists(updateReqVO.getId());
        // 更新
        DatasetTaskUserDO updateObj = BeanUtils.toBean(updateReqVO, DatasetTaskUserDO.class);
        taskUserMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetTaskUser(Long id) {
        // 校验存在
        validateDatasetTaskUserExists(id);
        // 删除
        taskUserMapper.deleteById(id);
    }

    private void validateDatasetTaskUserExists(Long id) {
        if (taskUserMapper.selectById(id) == null) {
            throw exception(DATASET_TASK_USER_NOT_EXISTS);
        }
    }

    @Override
    public DatasetTaskUserDO getDatasetTaskUser(Long id) {
        return taskUserMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetTaskUserDO> getDatasetTaskUserPage(DatasetTaskUserPageReqVO pageReqVO) {
        return taskUserMapper.selectPage(pageReqVO);
    }

}