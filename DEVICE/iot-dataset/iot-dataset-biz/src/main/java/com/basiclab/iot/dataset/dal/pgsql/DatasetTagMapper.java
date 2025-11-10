package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTagDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTagPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 数据集标签 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetTagMapper extends BaseMapperX<DatasetTagDO> {

    default PageResult<DatasetTagDO> selectPage(DatasetTagPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetTagDO>()
                .eqIfPresent(DatasetTagDO::getShortcut, reqVO.getShortcut())
                .likeIfPresent(DatasetTagDO::getName, reqVO.getName())
                .eqIfPresent(DatasetTagDO::getColor, reqVO.getColor())
                .eqIfPresent(DatasetTagDO::getDatasetId, reqVO.getDatasetId())
                .eqIfPresent(DatasetTagDO::getWarehouseId, reqVO.getWarehouseId())
                .eqIfPresent(DatasetTagDO::getDescription, reqVO.getDescription())
                .orderByDesc(DatasetTagDO::getUpdateTime));
    }

}