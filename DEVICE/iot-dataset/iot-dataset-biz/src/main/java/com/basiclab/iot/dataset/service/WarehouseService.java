package com.basiclab.iot.dataset.service;

import javax.validation.*;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehousePageReqVO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseSaveReqVO;

/**
 * 数据仓 Service 接口
 *
 * @author EasyAIoT
 */
public interface WarehouseService {

    /**
     * 创建数据仓
     *
     * @param createReqVO 创建信息
     * @return 编号
     */
    Long createWarehouse(@Valid WarehouseSaveReqVO createReqVO);

    /**
     * 更新数据仓
     *
     * @param updateReqVO 更新信息
     */
    void updateWarehouse(@Valid WarehouseSaveReqVO updateReqVO);

    /**
     * 删除数据仓
     *
     * @param id 编号
     */
    void deleteWarehouse(Long id);

    /**
     * 获得数据仓
     *
     * @param id 编号
     * @return 数据仓
     */
    WarehouseDO getWarehouse(Long id);

    /**
     * 获得数据仓分页
     *
     * @param pageReqVO 分页查询
     * @return 数据仓分页
     */
    PageResult<WarehouseDO> getWarehousePage(WarehousePageReqVO pageReqVO);

}