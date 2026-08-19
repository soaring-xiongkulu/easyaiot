package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.EdgeNodeDO;
import com.basiclab.iot.node.domain.vo.EdgeNodePageReqVO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface EdgeNodeMapper extends BaseMapperX<EdgeNodeDO> {

    default PageResult<EdgeNodeDO> selectPage(EdgeNodePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<EdgeNodeDO>()
                .likeIfPresent(EdgeNodeDO::getName, reqVO.getName())
                .likeIfPresent(EdgeNodeDO::getHost, reqVO.getHost())
                .eqIfPresent(EdgeNodeDO::getStatus, reqVO.getStatus())
                .eqIfPresent(EdgeNodeDO::getEnabled, reqVO.getEnabled())
                .orderByDesc(EdgeNodeDO::getUpdateTime));
    }

    default EdgeNodeDO selectByComputeNodeId(Long computeNodeId) {
        return selectOne(EdgeNodeDO::getComputeNodeId, computeNodeId);
    }

    default EdgeNodeDO selectByHost(String host) {
        return selectOne(EdgeNodeDO::getHost, host);
    }

}
