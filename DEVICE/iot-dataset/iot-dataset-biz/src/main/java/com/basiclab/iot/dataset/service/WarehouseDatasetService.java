package com.basiclab.iot.dataset.service;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDatasetDO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetPageReqVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetSaveReqVO;

import javax.validation.Valid;

/**
 * 数据仓数据集关联 Service 接口
 *
 * @author EasyAIoT
 */
public interface WarehouseDatasetService {

    /**
     * 创建数据仓数据集关联
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createWarehouseDataset(@Valid WarehouseDatasetSaveReqVO createReqVO);

    /**
     * 更新数据仓数据集关联
     *
     * @param updateReqVO 更新信息
     */
    void updateWarehouseDataset(@Valid WarehouseDatasetSaveReqVO updateReqVO);

    /**
     * 删除数据仓数据集关联
     *
     * @param id 编号
     */
    void deleteWarehouseDataset(Long id);

    /**
     * 获得数据仓数据集关联
     *
     * @param id 编号
     * @return 数据仓数据集关联
     */
    WarehouseDatasetDO getWarehouseDataset(Long id);

    /**
     * 获得数据仓数据集关联分页
     *
     * @param pageReqVO 分页查询
     * @return 数据仓数据集关联分页
     */
    PageResult<WarehouseDatasetDO> getWarehouseDatasetPage(WarehouseDatasetPageReqVO pageReqVO);

}