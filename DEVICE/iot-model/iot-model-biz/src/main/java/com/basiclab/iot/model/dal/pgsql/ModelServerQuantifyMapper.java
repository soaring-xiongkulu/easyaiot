package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerQuantifyDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerQuantifyPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型量化服务 Mapper
 *
 * @author EasyAIoT
 */
@Mapper
public interface ModelServerQuantifyMapper extends BaseMapperX<ModelServerQuantifyDO> {

    default PageResult<ModelServerQuantifyDO> selectPage(ModelServerQuantifyPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerQuantifyDO>()
                .eqIfPresent(ModelServerQuantifyDO::getModelServeId, reqVO.getModelServeId())
                .eqIfPresent(ModelServerQuantifyDO::getModelId, reqVO.getModelId())
                .eqIfPresent(ModelServerQuantifyDO::getModelTypeId, reqVO.getModelTypeId())
                .eqIfPresent(ModelServerQuantifyDO::getVersion, reqVO.getVersion())
                .betweenIfPresent(ModelServerQuantifyDO::getQuantifyTime, reqVO.getQuantifyTime())
                .eqIfPresent(ModelServerQuantifyDO::getQuantifyState, reqVO.getQuantifyState())
                .eqIfPresent(ModelServerQuantifyDO::getPackState, reqVO.getPackState())
                .eqIfPresent(ModelServerQuantifyDO::getQuantifyFileUrl, reqVO.getQuantifyFileUrl())
                .eqIfPresent(ModelServerQuantifyDO::getEdgePlatform, reqVO.getEdgePlatform())
                .eqIfPresent(ModelServerQuantifyDO::getChipModel, reqVO.getChipModel())
                .eqIfPresent(ModelServerQuantifyDO::getRunEnvironment, reqVO.getRunEnvironment())
                .eqIfPresent(ModelServerQuantifyDO::getDevLanguage, reqVO.getDevLanguage())
                .eqIfPresent(ModelServerQuantifyDO::getApplyType, reqVO.getApplyType())
                .eqIfPresent(ModelServerQuantifyDO::getGiteeUrl, reqVO.getGiteeUrl())
                .eqIfPresent(ModelServerQuantifyDO::getReason, reqVO.getReason())
                .eqIfPresent(ModelServerQuantifyDO::getQuantifyDescription, reqVO.getQuantifyDescription())
                .eqIfPresent(ModelServerQuantifyDO::getRknnDir, reqVO.getRknnDir())
                .orderByDesc(ModelServerQuantifyDO::getUpdateTime));
    }

}