package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetVideoDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetVideoPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 视频数据集 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetVideoMapper extends BaseMapperX<DatasetVideoDO> {

    default PageResult<DatasetVideoDO> selectPage(DatasetVideoPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetVideoDO>()
                .eqIfPresent(DatasetVideoDO::getDatasetId, reqVO.getDatasetId())
                .eqIfPresent(DatasetVideoDO::getVideoPath, reqVO.getVideoPath())
                .eqIfPresent(DatasetVideoDO::getCoverPath, reqVO.getCoverPath())
                .likeIfPresent(DatasetVideoDO::getName, reqVO.getName())
                .eqIfPresent(DatasetVideoDO::getDescription, reqVO.getDescription())
                .orderByDesc(DatasetVideoDO::getUpdateTime));
    }

}