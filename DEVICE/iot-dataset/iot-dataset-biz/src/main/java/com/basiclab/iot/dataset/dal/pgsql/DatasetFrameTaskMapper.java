package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetFrameTaskDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetFrameTaskPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 视频流帧捕获任务 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetFrameTaskMapper extends BaseMapperX<DatasetFrameTaskDO> {

    default PageResult<DatasetFrameTaskDO> selectPage(DatasetFrameTaskPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetFrameTaskDO>()
                .eqIfPresent(DatasetFrameTaskDO::getDatasetId, reqVO.getDatasetId())
                .likeIfPresent(DatasetFrameTaskDO::getTaskName, reqVO.getTaskName())
                .eqIfPresent(DatasetFrameTaskDO::getTaskCode, reqVO.getTaskCode())
                .eqIfPresent(DatasetFrameTaskDO::getTaskType, reqVO.getTaskType())
                .eqIfPresent(DatasetFrameTaskDO::getChannelId, reqVO.getChannelId())
                .eqIfPresent(DatasetFrameTaskDO::getDeviceId, reqVO.getDeviceId())
                .eqIfPresent(DatasetFrameTaskDO::getRtmpUrl, reqVO.getRtmpUrl())
                .eqIfPresent(DatasetFrameTaskDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(DatasetFrameTaskDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(DatasetFrameTaskDO::getUpdateBy, reqVO.getUpdateBy())
                .orderByDesc(DatasetFrameTaskDO::getId));
    }

}