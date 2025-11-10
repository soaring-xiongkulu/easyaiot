package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetPageReqVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 数据集 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetMapper extends BaseMapperX<DatasetDO> {

    default PageResult<DatasetDO> selectPage(DatasetPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetDO>()
                .eqIfPresent(DatasetDO::getDatasetCode, reqVO.getDatasetCode())
                .likeIfPresent(DatasetDO::getName, reqVO.getName())
                .eqIfPresent(DatasetDO::getCoverPath, reqVO.getCoverPath())
                .eqIfPresent(DatasetDO::getDescription, reqVO.getDescription())
                .eqIfPresent(DatasetDO::getDatasetType, reqVO.getDatasetType())
                .eqIfPresent(DatasetDO::getAudit, reqVO.getAudit())
                .eqIfPresent(DatasetDO::getReason, reqVO.getReason())
                .orderByDesc(DatasetDO::getUpdateTime));
    }

    // 分页查询数据集列表（带统计字段）
    List<DatasetDO> getDatasetList(@Param("reqVO") DatasetPageReqVO reqVO);

    // 查询单个数据集详情（带统计字段）
    DatasetDO getDataset(@Param("datasetId") Long datasetId);
}