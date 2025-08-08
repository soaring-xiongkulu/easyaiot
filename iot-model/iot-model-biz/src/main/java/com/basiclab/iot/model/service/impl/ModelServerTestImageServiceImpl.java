package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestImageDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerTestImageMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImagePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImageSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestImageService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_TEST_IMAGE_NOT_EXISTS;

/**
 * 模型测试图片 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServerTestImageServiceImpl implements ModelServerTestImageService {

    @Resource
    private ModelServerTestImageMapper modelServerTestImageMapper;

    @Override
    public Long createModelServerTestImage(ModelServerTestImageSaveReqVO createReqVO) {
        // 插入
        ModelServerTestImageDO serverTestImage = BeanUtils.toBean(createReqVO, ModelServerTestImageDO.class);
        modelServerTestImageMapper.insert(serverTestImage);
        // 返回
        return serverTestImage.getId();
    }

    @Override
    public void updateModelServerTestImage(ModelServerTestImageSaveReqVO updateReqVO) {
        // 校验存在
        validateModelServerTestImageExists(updateReqVO.getId());
        // 更新
        ModelServerTestImageDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerTestImageDO.class);
        modelServerTestImageMapper.updateById(updateObj);
    }

    @Override
    public void deleteModelServerTestImage(Long id) {
        // 校验存在
        validateModelServerTestImageExists(id);
        // 删除
        modelServerTestImageMapper.deleteById(id);
    }

    private void validateModelServerTestImageExists(Long id) {
        if (modelServerTestImageMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_TEST_IMAGE_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerTestImageDO getModelServerTestImage(Long id) {
        return modelServerTestImageMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerTestImageDO> getModelServerTestImagePage(ModelServerTestImagePageReqVO pageReqVO) {
        return modelServerTestImageMapper.selectPage(pageReqVO);
    }

}