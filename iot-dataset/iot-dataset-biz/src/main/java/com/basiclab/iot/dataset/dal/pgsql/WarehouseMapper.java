package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.WarehouseDO;
import com.basiclab.iot.dataset.domain.warehouse.vo.WarehousePageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 数据仓 Mapper
 *
 * @author IoT
 */
@Mapper
public interface WarehouseMapper extends BaseMapperX<WarehouseDO> {

    default PageResult<WarehouseDO> selectPage(WarehousePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<WarehouseDO>()
                .likeIfPresent(WarehouseDO::getName, reqVO.getName())
                .eqIfPresent(WarehouseDO::getCoverPath, reqVO.getCoverPath())
                .eqIfPresent(WarehouseDO::getDescription, reqVO.getDescription())
                .orderByDesc(WarehouseDO::getUpdateTime));
    }

}