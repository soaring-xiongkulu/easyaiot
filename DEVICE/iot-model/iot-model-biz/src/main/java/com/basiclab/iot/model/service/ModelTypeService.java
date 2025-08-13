package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelTypeDO;
import com.basiclab.iot.model.domain.model.vo.ModelTypePageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelTypeSaveReqVO;

import javax.validation.Valid;

/**
 * 模型类型 Service 接口
 *
 * @author EasyAIoT
 */
public interface ModelTypeService {

    /**
     * 创建模型类型
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModelType(@Valid ModelTypeSaveReqVO createReqVO);

    /**
     * 更新模型类型
     *
     * @param updateReqVO 更新信息
     */
    void updateModelType(@Valid ModelTypeSaveReqVO updateReqVO);

    /**
     * 删除模型类型
     *
     * @param id 编号
     */
    void deleteModelType(Long id);

    /**
     * 获得模型类型
     *
     * @param id 编号
     * @return 模型类型
     */
    ModelTypeDO getModelType(Long id);

    /**
     * 获得模型类型分页
     *
     * @param pageReqVO 分页查询
     * @return 模型类型分页
     */
    PageResult<ModelTypeDO> getModelTypePage(ModelTypePageReqVO pageReqVO);

}