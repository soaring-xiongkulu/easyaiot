package com.basiclab.iot.dataset.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetTagMapper;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagSaveReqVO;
import com.basiclab.iot.dataset.service.DatasetTagService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TAG_NOT_EXISTS;
import static com.basiclab.iot.dataset.enums.ErrorCodeConstants.DATASET_TAG_NUMBER_EXISTS;

/**
 * 数据集标签 Service 实现类
 *
 * @author IoT
 */
@Service
@Validated
public class DatasetTagServiceImpl implements DatasetTagService {

    @Resource
    private DatasetTagMapper tagMapper;

    @Override
    public Long createDatasetTag(DatasetTagSaveReqVO createReqVO) {
        // 在当前数据集ID，快捷键不能重复
        LambdaQueryWrapper<DatasetTagDO> wrapper = Wrappers.lambdaQuery();
        wrapper.eq(DatasetTagDO::getDatasetId, createReqVO.getDatasetId());
        wrapper.eq(DatasetTagDO::getShortcut, createReqVO.getShortcut());
        if (tagMapper.selectOne(wrapper) != null) {
            throw exception(DATASET_TAG_NUMBER_EXISTS);
        }
        // 插入
        DatasetTagDO tag = BeanUtils.toBean(createReqVO, DatasetTagDO.class);
        tagMapper.insert(tag);
        // 返回
        return tag.getId();
    }

    @Override
    public void updateDatasetTag(DatasetTagSaveReqVO updateReqVO) {
        // 校验存在
        validateDatasetTagExists(updateReqVO.getId());
        // 在当前数据集ID，快捷键不能重复
        LambdaQueryWrapper<DatasetTagDO> wrapper = Wrappers.lambdaQuery();
        wrapper.eq(DatasetTagDO::getDatasetId, updateReqVO.getDatasetId());
        wrapper.eq(DatasetTagDO::getShortcut, updateReqVO.getShortcut());
        DatasetTagDO datasetTagDO = tagMapper.selectOne(wrapper);
        if (datasetTagDO != null && !datasetTagDO.getId().equals(updateReqVO.getId())) {
            throw exception(DATASET_TAG_NUMBER_EXISTS);
        }
        // 更新
        DatasetTagDO updateObj = BeanUtils.toBean(updateReqVO, DatasetTagDO.class);
        tagMapper.updateById(updateObj);
    }

    @Override
    public void deleteDatasetTag(Long id) {
        // 校验存在
        validateDatasetTagExists(id);
        // 删除
        tagMapper.deleteById(id);
    }

    private void validateDatasetTagExists(Long id) {
        if (tagMapper.selectById(id) == null) {
            throw exception(DATASET_TAG_NOT_EXISTS);
        }
    }

    @Override
    public DatasetTagDO getDatasetTag(Long id) {
        return tagMapper.selectById(id);
    }

    @Override
    public PageResult<DatasetTagDO> getDatasetTagPage(DatasetTagPageReqVO pageReqVO) {
        return tagMapper.selectPage(pageReqVO);
    }

}