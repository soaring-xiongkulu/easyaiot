package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型测试服务 Mapper
 *
 * @author EasyAIoT
 */
@Mapper
public interface ModelServerTestMapper extends BaseMapperX<ModelServerTestDO> {

    default PageResult<ModelServerTestDO> selectPage(ModelServerTestPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerTestDO>()
                .eqIfPresent(ModelServerTestDO::getModelServeId, reqVO.getModelServeId())
                .eqIfPresent(ModelServerTestDO::getModelId, reqVO.getModelId())
                .likeIfPresent(ModelServerTestDO::getName, reqVO.getName())
                .eqIfPresent(ModelServerTestDO::getType, reqVO.getType())
                .eqIfPresent(ModelServerTestDO::getPlannedQuantity, reqVO.getPlannedQuantity())
                .eqIfPresent(ModelServerTestDO::getMarkedQuantity, reqVO.getMarkedQuantity())
                .eqIfPresent(ModelServerTestDO::getNotTargetCount, reqVO.getNotTargetCount())
                .betweenIfPresent(ModelServerTestDO::getFinishTime, reqVO.getFinishTime())
                .eqIfPresent(ModelServerTestDO::getState, reqVO.getState())
                .eqIfPresent(ModelServerTestDO::getDescription, reqVO.getDescription())
                .orderByDesc(ModelServerTestDO::getUpdateTime));
    }

}