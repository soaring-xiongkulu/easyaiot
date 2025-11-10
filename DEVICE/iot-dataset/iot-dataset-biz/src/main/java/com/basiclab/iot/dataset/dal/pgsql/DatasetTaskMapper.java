package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 标注任务 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetTaskMapper extends BaseMapperX<DatasetTaskDO> {

    default PageResult<DatasetTaskDO> selectPage(DatasetTaskPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetTaskDO>()
                .likeIfPresent(DatasetTaskDO::getName, reqVO.getName())
                .eqIfPresent(DatasetTaskDO::getDatasetId, reqVO.getDatasetId())
                .eqIfPresent(DatasetTaskDO::getDataRange, reqVO.getDataRange())
                .eqIfPresent(DatasetTaskDO::getPlannedQuantity, reqVO.getPlannedQuantity())
                .eqIfPresent(DatasetTaskDO::getMarkedQuantity, reqVO.getMarkedQuantity())
                .eqIfPresent(DatasetTaskDO::getNewLabel, reqVO.getNewLabel())
                .eqIfPresent(DatasetTaskDO::getFinishStatus, reqVO.getFinishStatus())
                .betweenIfPresent(DatasetTaskDO::getFinishTime, reqVO.getFinishTime())
                .eqIfPresent(DatasetTaskDO::getModelId, reqVO.getModelId())
                .eqIfPresent(DatasetTaskDO::getModelServeId, reqVO.getModelServeId())
                .eqIfPresent(DatasetTaskDO::getIsStop, reqVO.getIsStop())
                .eqIfPresent(DatasetTaskDO::getTaskType, reqVO.getTaskType())
                .betweenIfPresent(DatasetTaskDO::getEndTime, reqVO.getEndTime())
                .eqIfPresent(DatasetTaskDO::getNotTargetCount, reqVO.getNotTargetCount())
                .orderByDesc(DatasetTaskDO::getUpdateTime));
    }

}