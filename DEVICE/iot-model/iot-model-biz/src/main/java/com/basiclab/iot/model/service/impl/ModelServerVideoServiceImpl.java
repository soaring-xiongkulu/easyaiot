package com.basiclab.iot.model.service.impl;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.model.dal.dataobject.ModelServerVideoDO;
import com.basiclab.iot.model.dal.pgsql.ModelServerVideoMapper;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoSaveReqVO;
import com.basiclab.iot.model.service.ModelServerVideoService;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import javax.annotation.Resource;

import static com.basiclab.iot.common.exception.util.ServiceExceptionUtil.exception;
import static com.basiclab.iot.model.enums.ErrorCodeConstants.MODEL_SERVER_VIDEO_NOT_EXISTS;

/**
 * 模型服务视频 Service 实现类
 *
 * @author EasyAIoT
 */
@Service
@Validated
public class ModelServerVideoServiceImpl implements ModelServerVideoService {

    @Resource
    private ModelServerVideoMapper modelServerVideoMapper;

    @Override
    public Long createModelServerVideo(ModelServerVideoSaveReqVO createReqVO) {
        // 插入
        ModelServerVideoDO serverVideo = BeanUtils.toBean(createReqVO, ModelServerVideoDO.class);
        modelServerVideoMapper.insert(serverVideo);
        // 返回
        return serverVideo.getId();
    }

    @Override
    public void updateModelServerVideo(ModelServerVideoSaveReqVO updateReqVO) {
        // 校验存在
        validateModelServerVideoExists(updateReqVO.getId());
        // 更新
        ModelServerVideoDO updateObj = BeanUtils.toBean(updateReqVO, ModelServerVideoDO.class);
        modelServerVideoMapper.updateById(updateObj);
    }

    @Override
    public void deleteModelServerVideo(Long id) {
        // 校验存在
        validateModelServerVideoExists(id);
        // 删除
        modelServerVideoMapper.deleteById(id);
    }

    private void validateModelServerVideoExists(Long id) {
        if (modelServerVideoMapper.selectById(id) == null) {
            throw exception(MODEL_SERVER_VIDEO_NOT_EXISTS);
        }
    }

    @Override
    public ModelServerVideoDO getModelServerVideo(Long id) {
        return modelServerVideoMapper.selectById(id);
    }

    @Override
    public PageResult<ModelServerVideoDO> getModelServerVideoPage(ModelServerVideoPageReqVO pageReqVO) {
        return modelServerVideoMapper.selectPage(pageReqVO);
    }

}