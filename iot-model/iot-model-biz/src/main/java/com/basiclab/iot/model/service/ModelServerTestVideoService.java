package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoSaveReqVO;

import javax.validation.Valid;

/**
 * 模型测试视频 Service 接口
 *
 * @author IoT
 */
public interface ModelServerTestVideoService {

    /**
     * 创建模型测试视频
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModelServerTestVideo(@Valid ModelServerTestVideoSaveReqVO createReqVO);

    /**
     * 更新模型测试视频
     *
     * @param updateReqVO 更新信息
     */
    void updateModelServerTestVideo(@Valid ModelServerTestVideoSaveReqVO updateReqVO);

    /**
     * 删除模型测试视频
     *
     * @param id 编号
     */
    void deleteModelServerTestVideo(Long id);

    /**
     * 获得模型测试视频
     *
     * @param id 编号
     * @return 模型测试视频
     */
    ModelServerTestVideoDO getModelServerTestVideo(Long id);

    /**
     * 获得模型测试视频分页
     *
     * @param pageReqVO 分页查询
     * @return 模型测试视频分页
     */
    PageResult<ModelServerTestVideoDO> getModelServerTestVideoPage(ModelServerTestVideoPageReqVO pageReqVO);

}