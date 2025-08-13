package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestVideoDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerTestVideoMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoSaveReqVO;
import com.basiclab.iot.model.service.ModelServerTestVideoService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_TEST_VIDEO_NOT_EXISTS;

/**
 * 模型测试视频 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServerTestVideoServiceImpl implements ModelServerTestVideoService {

    @Resource
    private ModelServerTestVideoMapper modelServerTestVideoMapper;

    @Override
    public Long createModelServerTestVideo(ModelServerTestVideoSaveReqVO createReqVO) {
        // 插入
        ModelServerTestVideoDO serverTestVideo = BeanUtils.toBean(createReqVO, ModelServerTestVideoDO.class);
        modelServerTestVideoMapper.insert(serverTestVideo);
        // 返回
        return serverTestVideo.getId();
    }

    @Override
    public void updateModelServerTestVideo(ModelServerTestVideoSaveReqVO updateReqVO) {
        // 校验存在
        validateModelServerTestVideoExists(updateReqVO.getId());
        // 更新
        ModelServerTestVideoDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerTestVideoDO.class);
        modelServerTestVideoMapper.updateById(updateObj);
    }

    @Override
    public void deleteModelServerTestVideo(Long id) {
        // 校验存在
        validateModelServerTestVideoExists(id);
        // 删除
        modelServerTestVideoMapper.deleteById(id);
    }

    private void validateModelServerTestVideoExists(Long id) {
        if (modelServerTestVideoMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_TEST_VIDEO_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerTestVideoDO getModelServerTestVideo(Long id) {
        return modelServerTestVideoMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerTestVideoDO> getModelServerTestVideoPage(ModelServerTestVideoPageReqVO pageReqVO) {
        return modelServerTestVideoMapper.selectPage(pageReqVO);
    }

}