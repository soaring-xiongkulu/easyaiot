package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestSaveReqVO;

import javax.validation.Valid;

/**
 * 模型测试服务 Service 接口
 *
 * @author EasyAIoT
 */
public interface ModelServerTestService {

    /**
     * 创建模型测试服务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createModelServerTest(@Valid ModelServerTestSaveReqVO createReqVO);

    /**
     * 更新模型测试服务
     *
     * @param updateReqVO 更新信息
     */
    void updateModelServerTest(@Valid ModelServerTestSaveReqVO updateReqVO);

    /**
     * 删除模型测试服务
     *
     * @param id 编号
     */
    void deleteModelServerTest(Long id);

    /**
     * 获得模型测试服务
     *
     * @param id 编号
     * @return 模型测试服务
     */
    ModelServerTestDO getModelServerTest(Long id);

    /**
     * 获得模型测试服务分页
     *
     * @param pageReqVO 分页查询
     * @return 模型测试服务分页
     */
    PageResult<ModelServerTestDO> getModelServerTestPage(ModelServerTestPageReqVO pageReqVO);

}