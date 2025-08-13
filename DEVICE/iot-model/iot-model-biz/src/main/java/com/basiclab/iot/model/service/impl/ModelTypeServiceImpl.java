package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelTypeDO;
import com.basiclab.iot.model.dal.pgsql.ModelTypeMapper;
import com.basiclab.iot.model.domain.model.vo.ModelTypePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelTypeSaveReqVO;
import com.basiclab.iot.model.service.ModelTypeService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_TYPE_NOT_EXISTS;

/**
 * 模型类型 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelTypeServiceImpl implements ModelTypeService {

    @Resource
    private ModelTypeMapper modelTypeMapper;

    @Override
    public Long createModelType(ModelTypeSaveReqVO createReqVO) {
        // 插入
        ModelTypeDO type = BeanUtils.toBean(createReqVO, ModelTypeDO.class);
        modelTypeMapper.insert(type);
        // 返回
        return type.getId();
    }

    @Override
    public void updateModelType(ModelTypeSaveReqVO updateReqVO) {
        // 校验存在
        validateModelTypeExists(updateReqVO.getId());
        // 更新
        ModelTypeDO updateObj = BeanUtils.toBean(updateReqVO, ModelTypeDO.class);
        modelTypeMapper.updateById(updateObj);
    }

    @Override
    public void deleteModelType(Long id) {
        // 校验存在
        validateModelTypeExists(id);
        // 删除
        modelTypeMapper.deleteById(id);
    }

    private void validateModelTypeExists(Long id) {
        if (modelTypeMapper.selectById(id) == null) {
            throw exception(MODEL_TYPE_NOT_EXISTS);
        }
    }

    @Override
    public ModelTypeDO getModelType(Long id) {
        return modelTypeMapper.selectById(id);
    }

    @Override
    public PageResult<ModelTypeDO> getModelTypePage(ModelTypePageReqVO pageReqVO) {
        return modelTypeMapper.selectPage(pageReqVO);
    }

}