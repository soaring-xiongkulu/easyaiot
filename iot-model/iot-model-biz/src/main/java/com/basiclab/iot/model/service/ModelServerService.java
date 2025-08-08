package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerSaveReqVO;

import javax.validation.Valid;

/**
 * 模型服务 Service 接口
 *
 * @author EasyAIoT
 */
public interface ModelServerService {

    /**
     * 创建模型服务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createServer(@Valid ModelServerSaveReqVO createReqVO);

    /**
     * 更新模型服务
     *
     * @param updateReqVO 更新信息
     */
    void updateServer(@Valid ModelServerSaveReqVO updateReqVO);

    /**
     * 删除模型服务
     *
     * @param id 编号
     */
    void deleteServer(Long id);

    /**
     * 获得模型服务
     *
     * @param id 编号
     * @return 模型服务
     */
    ModelServerDO getServer(Long id);

    /**
     * 获得模型服务分页
     *
     * @param pageReqVO 分页查询
     * @return 模型服务分页
     */
    PageResult<ModelServerDO> getServerPage(ModelServerPageReqVO pageReqVO);

}