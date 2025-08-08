package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.model.dal.dataobject.ModelServerDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型服务 Mapper
 *
 * @author IoT
 */
@Mapper
public interface ModelServerMapper extends BaseMapperX<ModelServerDO> {

    default PageResult<ModelServerDO> selectPage(ModelServerPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerDO>()
                .likeIfPresent(ModelServerDO::getName, reqVO.getName())
                .eqIfPresent(ModelServerDO::getModelId, reqVO.getModelId())
                .eqIfPresent(ModelServerDO::getDatasetId, reqVO.getDatasetId())
                .eqIfPresent(ModelServerDO::getPublishStatus, reqVO.getPublishStatus())
                .eqIfPresent(ModelServerDO::getAuditUserId, reqVO.getAuditUserId())
                .eqIfPresent(ModelServerDO::getVersion, reqVO.getVersion())
                .eqIfPresent(ModelServerDO::getServerAddress, reqVO.getServerAddress())
                .eqIfPresent(ModelServerDO::getOnnxFileUrl, reqVO.getOnnxFileUrl())
                .eqIfPresent(ModelServerDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ModelServerDO::getSize, reqVO.getSize())
                .eqIfPresent(ModelServerDO::getExecuteStatus, reqVO.getExecuteStatus())
                .betweenIfPresent(ModelServerDO::getPublishTime, reqVO.getPublishTime())
                .eqIfPresent(ModelServerDO::getAnchorsFileUrl, reqVO.getAnchorsFileUrl())
                .eqIfPresent(ModelServerDO::getApplyFileUrl, reqVO.getApplyFileUrl())
                .eqIfPresent(ModelServerDO::getApplyFileSize, reqVO.getApplyFileSize())
                .eqIfPresent(ModelServerDO::getApplyFileMd5, reqVO.getApplyFileMd5())
                .orderByDesc(ModelServerDO::getUpdateTime));
    }

}