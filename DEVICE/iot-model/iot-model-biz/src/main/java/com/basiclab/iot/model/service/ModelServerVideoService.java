package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoSaveReqVO;

import javax.validation.Valid;

/**
 * 模型服务视频 Service 接口
 *
 * @author EasyAIoT
 */
public interface ModelServerVideoService {

    /**
     * 创建模型服务视频
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModelServerVideo(@Valid ModelServerVideoSaveReqVO createReqVO);

    /**
     * 更新模型服务视频
     *
     * @param updateReqVO 更新信息
     */
    void updateModelServerVideo(@Valid ModelServerVideoSaveReqVO updateReqVO);

    /**
     * 删除模型服务视频
     *
     * @param id 编号
     */
    void deleteModelServerVideo(Long id);

    /**
     * 获得模型服务视频
     *
     * @param id 编号
     * @return 模型服务视频
     */
    ModelServerVideoDO getModelServerVideo(Long id);

    /**
     * 获得模型服务视频分页
     *
     * @param pageReqVO 分页查询
     * @return 模型服务视频分页
     */
    PageResult<ModelServerVideoDO> getModelServerVideoPage(ModelServerVideoPageReqVO pageReqVO);

}