package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelDO;
import com.basiclab.iot.model.dal.pgsql.ModelMapper;
import com.basiclab.iot.model.domain.model.vo.ModelPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelSaveReqVO;
import com.basiclab.iot.model.service.ModelService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_NOT_EXISTS;

/**
 * 模型 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServiceImpl implements ModelService {

    @Resource
    private ModelMapper modelMapper;

    @Override
    public Long createModel(ModelSaveReqVO createReqVO) {
        // 插入
        ModelDO model = BeanUtils.toBean(createReqVO, ModelDO.class);
        modelMapper.insert(model);
        // 返回
        return model.getId();
    }

    @Override
    public void updateModel(ModelSaveReqVO updateReqVO) {
        // 校验存在
        validateExists(updateReqVO.getId());
        // 更新
        ModelDO updateObj = BeanUtils.toBean(updateReqVO, ModelDO.class);
        modelMapper.updateById(updateObj);
    }

    @Override
    public void deleteModel(Long id) {
        // 校验存在
        validateExists(id);
        // 删除
        modelMapper.deleteById(id);
    }

    private void validateExists(Long id) {
        if (modelMapper.selectById(id) == null) {
            throw exception(MODEL_NOT_EXISTS);
        }
    }

    @Override
    public ModelDO getModel(Long id) {
        return modelMapper.selectById(id);
    }

    @Override
    public PageResult<ModelDO> getModelPage(ModelPageReqVO pageReqVO) {
        return modelMapper.selectPage(pageReqVO);
    }

}