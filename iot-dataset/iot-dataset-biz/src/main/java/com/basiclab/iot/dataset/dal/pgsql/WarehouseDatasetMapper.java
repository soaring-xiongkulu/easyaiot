package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDatasetDO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehouseDatasetPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 数据仓数据集关联 Mapper
 *
 * @author IoT
 */
@Mapper
public interface WarehouseDatasetMapper extends BaseMapperX<WarehouseDatasetDO> {

    default PageResult<WarehouseDatasetDO> selectPage(WarehouseDatasetPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<WarehouseDatasetDO>()
                .eqIfPresent(WarehouseDatasetDO::getDatasetId, reqVO.getDatasetId())
                .eqIfPresent(WarehouseDatasetDO::getWarehouseId, reqVO.getWarehouseId())
                .eqIfPresent(WarehouseDatasetDO::getPlanSyncCount, reqVO.getPlanSyncCount())
                .eqIfPresent(WarehouseDatasetDO::getSyncCount, reqVO.getSyncCount())
                .eqIfPresent(WarehouseDatasetDO::getSyncStatus, reqVO.getSyncStatus())
                .eqIfPresent(WarehouseDatasetDO::getFailCount, reqVO.getFailCount())
                .orderByDesc(WarehouseDatasetDO::getUpdateTime));
    }

}