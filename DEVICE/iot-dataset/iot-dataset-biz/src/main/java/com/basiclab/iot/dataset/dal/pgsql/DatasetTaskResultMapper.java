package com.basiclab.iot.dataset.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.dataset.dal.dataobject.DatasetTaskResultDO;
import com.basiclab.iot.dataset.domain.dataset.vo.DatasetTaskResultPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 标注任务结果 Mapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface DatasetTaskResultMapper extends BaseMapperX<DatasetTaskResultDO> {

    default PageResult<DatasetTaskResultDO> selectPage(DatasetTaskResultPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DatasetTaskResultDO>()
                .eqIfPresent(DatasetTaskResultDO::getDatasetImageId, reqVO.getDatasetImageId())
                .eqIfPresent(DatasetTaskResultDO::getModelId, reqVO.getModelId())
                .eqIfPresent(DatasetTaskResultDO::getHasAnno, reqVO.getHasAnno())
                .eqIfPresent(DatasetTaskResultDO::getAnnos, reqVO.getAnnos())
                .eqIfPresent(DatasetTaskResultDO::getTaskType, reqVO.getTaskType())
                .eqIfPresent(DatasetTaskResultDO::getUserId, reqVO.getUserId())
                .eqIfPresent(DatasetTaskResultDO::getPassStatus, reqVO.getPassStatus())
                .eqIfPresent(DatasetTaskResultDO::getTaskId, reqVO.getTaskId())
                .eqIfPresent(DatasetTaskResultDO::getReason, reqVO.getReason())
                .betweenIfPresent(DatasetTaskResultDO::getIsUpdate, reqVO.getIsUpdate())
                .orderByDesc(DatasetTaskResultDO::getUpdateTime));
    }

}