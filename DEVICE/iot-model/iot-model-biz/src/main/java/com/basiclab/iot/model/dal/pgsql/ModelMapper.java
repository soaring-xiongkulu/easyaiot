package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelDO;
import com.basiclab.iot.model.domain.model.vo.ModelPageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型 Mapper
 *
 * @author EasyAIoT
 */
@Mapper
public interface ModelMapper extends BaseMapperX<ModelDO> {

    default PageResult<ModelDO> selectPage(ModelPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelDO>()
                .likeIfPresent(ModelDO::getName, reqVO.getName())
                .eqIfPresent(ModelDO::getDescription, reqVO.getDescription())
                .eqIfPresent(ModelDO::getCoverPath, reqVO.getCoverPath())
                .eqIfPresent(ModelDO::getVersion, reqVO.getVersion())
                .eqIfPresent(ModelDO::getPublishStatus, reqVO.getPublishStatus())
                .eqIfPresent(ModelDO::getEdgePlatform, reqVO.getEdgePlatform())
                .eqIfPresent(ModelDO::getChipModel, reqVO.getChipModel())
                .eqIfPresent(ModelDO::getRunEnvironment, reqVO.getRunEnvironment())
                .eqIfPresent(ModelDO::getDevLanguage, reqVO.getDevLanguage())
                .eqIfPresent(ModelDO::getGitUrl, reqVO.getGitUrl())
                .eqIfPresent(ModelDO::getPtModelUrl, reqVO.getPtModelUrl())
                .eqIfPresent(ModelDO::getPtResultUrl, reqVO.getPtResultUrl())
                .eqIfPresent(ModelDO::getOnnxModelUrl, reqVO.getOnnxModelUrl())
                .eqIfPresent(ModelDO::getOnnxResultUrl, reqVO.getOnnxResultUrl())
                .eqIfPresent(ModelDO::getRknnModelUrl, reqVO.getRknnModelUrl())
                .eqIfPresent(ModelDO::getRknnResultUrl, reqVO.getRknnResultUrl())
                .orderByDesc(ModelDO::getUpdateTime));
    }

}