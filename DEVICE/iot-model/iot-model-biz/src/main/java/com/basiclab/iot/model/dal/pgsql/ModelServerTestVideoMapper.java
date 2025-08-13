package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestVideoPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型测试视频 Mapper
 *
 * @author EasyAIoT
 */
@Mapper
public interface ModelServerTestVideoMapper extends BaseMapperX<ModelServerTestVideoDO> {

    default PageResult<ModelServerTestVideoDO> selectPage(ModelServerTestVideoPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerTestVideoDO>()
                .eqIfPresent(ModelServerTestVideoDO::getModelServerTestId, reqVO.getModelServerTestId())
                .eqIfPresent(ModelServerTestVideoDO::getModelId, reqVO.getModelId())
                .eqIfPresent(ModelServerTestVideoDO::getDatasetVideoId, reqVO.getDatasetVideoId())
                .betweenIfPresent(ModelServerTestVideoDO::getAnnoTime, reqVO.getAnnoTime())
                .eqIfPresent(ModelServerTestVideoDO::getAnnoVideoPath, reqVO.getAnnoVideoPath())
                .eqIfPresent(ModelServerTestVideoDO::getState, reqVO.getState())
                .orderByDesc(ModelServerTestVideoDO::getUpdateTime));
    }

}