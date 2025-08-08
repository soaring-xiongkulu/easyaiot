package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelDO;
import com.basiclab.iot.model.domain.model.vo.ModelPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelSaveReqVO;

import javax.validation.Valid;

/**
 * 模型 Service 接口
 *
 * @author IoT
 */
public interface ModelService {

    /**
     * 创建模型
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModel(@Valid ModelSaveReqVO createReqVO);

    /**
     * 更新模型
     *
     * @param updateReqVO 更新信息
     */
    void updateModel(@Valid ModelSaveReqVO updateReqVO);

    /**
     * 删除模型
     *
     * @param id 编号
     */
    void deleteModel(Long id);

    /**
     * 获得模型
     *
     * @param id 编号
     * @return 模型
     */
    ModelDO getModel(Long id);

    /**
     * 获得模型分页
     *
     * @param pageReqVO 分页查询
     * @return 模型分页
     */
    PageResult<ModelDO> getModelPage(ModelPageReqVO pageReqVO);

}