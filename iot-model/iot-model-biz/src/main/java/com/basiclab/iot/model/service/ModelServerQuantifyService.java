package com.basiclab.iot.model.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerQuantifyDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifyPageReqVO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifySaveReqVO;

import javax.validation.Valid;

/**
 * 模型量化服务 Service 接口
 *
 * @author IoT
 */
public interface ModelServerQuantifyService {

    /**
     * 创建模型量化服务
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createServerQuantify(@Valid ModelServerQuantifySaveReqVO createReqVO);

    /**
     * 更新模型量化服务
     *
     * @param updateReqVO 更新信息
     */
    void updateServerQuantify(@Valid ModelServerQuantifySaveReqVO updateReqVO);

    /**
     * 删除模型量化服务
     *
     * @param id 编号
     */
    void deleteServerQuantify(Long id);

    /**
     * 获得模型量化服务
     *
     * @param id 编号
     * @return 模型量化服务
     */
    ModelServerQuantifyDO getServerQuantify(Long id);

    /**
     * 获得模型量化服务分页
     *
     * @param pageReqVO 分页查询
     * @return 模型量化服务分页
     */
    PageResult<ModelServerQuantifyDO> getServerQuantifyPage(ModelServerQuantifyPageReqVO pageReqVO);

}