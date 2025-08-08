package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerVideoDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerVideoPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型服务视频 Mapper
 *
 * @author IoT
 */
@Mapper
public interface ModelServerVideoMapper extends BaseMapperX<ModelServerVideoDO> {

    default PageResult<ModelServerVideoDO> selectPage(ModelServerVideoPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerVideoDO>()
                .eqIfPresent(ModelServerVideoDO::getModelServerId, reqVO.getModelServerId())
                .eqIfPresent(ModelServerVideoDO::getModelId, reqVO.getModelId())
                .eqIfPresent(ModelServerVideoDO::getVideoPath, reqVO.getVideoPath())
                .eqIfPresent(ModelServerVideoDO::getAnnoVideoPath, reqVO.getAnnoVideoPath())
                .eqIfPresent(ModelServerVideoDO::getCoverPath, reqVO.getCoverPath())
                .eqIfPresent(ModelServerVideoDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ModelServerVideoDO::getVideoResolution, reqVO.getVideoResolution())
                .eqIfPresent(ModelServerVideoDO::getDuration, reqVO.getDuration())
                .eqIfPresent(ModelServerVideoDO::getSuffix, reqVO.getSuffix())
                .eqIfPresent(ModelServerVideoDO::getFileSize, reqVO.getFileSize())
                .orderByDesc(ModelServerVideoDO::getUpdateTime));
    }

}