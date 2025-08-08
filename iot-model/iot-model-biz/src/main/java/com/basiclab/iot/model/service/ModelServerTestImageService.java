package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestImageDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImagePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImageSaveReqVO;

import javax.validation.Valid;

/**
 * 模型测试图片 Service 接口
 *
 * @author EasyAIoT
 */
public interface ModelServerTestImageService {

    /**
     * 创建模型测试图片
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModelServerTestImage(@Valid ModelServerTestImageSaveReqVO createReqVO);

    /**
     * 更新模型测试图片
     *
     * @param updateReqVO 更新信息
     */
    void updateModelServerTestImage(@Valid ModelServerTestImageSaveReqVO updateReqVO);

    /**
     * 删除模型测试图片
     *
     * @param id 编号
     */
    void deleteModelServerTestImage(Long id);

    /**
     * 获得模型测试图片
     *
     * @param id 编号
     * @return 模型测试图片
     */
    ModelServerTestImageDO getModelServerTestImage(Long id);

    /**
     * 获得模型测试图片分页
     *
     * @param pageReqVO 分页查询
     * @return 模型测试图片分页
     */
    PageResult<ModelServerTestImageDO> getModelServerTestImagePage(ModelServerTestImagePageReqVO pageReqVO);

}