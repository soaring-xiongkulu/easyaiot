package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelServerTestImageDO;
import com.basiclab.iot.model.domain.model.vo.ModelServerTestImagePageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型测试图片 Mapper
 *
 * @author IoT
 */
@Mapper
public interface ModelServerTestImageMapper extends BaseMapperX<ModelServerTestImageDO> {

    default PageResult<ModelServerTestImageDO> selectPage(ModelServerTestImagePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelServerTestImageDO>()
                .eqIfPresent(ModelServerTestImageDO::getModelServerTestId, reqVO.getModelServerTestId())
                .eqIfPresent(ModelServerTestImageDO::getModelId, reqVO.getModelId())
                .eqIfPresent(ModelServerTestImageDO::getDatasetImageId, reqVO.getDatasetImageId())
                .betweenIfPresent(ModelServerTestImageDO::getAnnoTime, reqVO.getAnnoTime())
                .eqIfPresent(ModelServerTestImageDO::getAnnoImagePath, reqVO.getAnnoImagePath())
                .eqIfPresent(ModelServerTestImageDO::getModificationCount, reqVO.getModificationCount())
                .orderByDesc(ModelServerTestImageDO::getUpdateTime));
    }

}