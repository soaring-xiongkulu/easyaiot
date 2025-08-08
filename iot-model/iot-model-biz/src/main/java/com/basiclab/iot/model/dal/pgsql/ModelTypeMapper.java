package com.basiclab.iot.model.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.model.dal.dataobject.ModelTypeDO;
import com.basiclab.iot.model.domain.model.vo.ModelTypePageReqVO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 模型类型 Mapper
 *
 * @author EasyAIoT
 */
@Mapper
public interface ModelTypeMapper extends BaseMapperX<ModelTypeDO> {

    default PageResult<ModelTypeDO> selectPage(ModelTypePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ModelTypeDO>()
                .likeIfPresent(ModelTypeDO::getName, reqVO.getName())
                .eqIfPresent(ModelTypeDO::getType, reqVO.getType())
                .eqIfPresent(ModelTypeDO::getParentId, reqVO.getParentId())
                .orderByDesc(ModelTypeDO::getUpdateTime));
    }

}