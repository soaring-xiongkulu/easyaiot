package com.basiclab.iot.node.dal.pgsql;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.domain.vo.ComputeNodePageReqVO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ComputeNodeMapper extends BaseMapperX<ComputeNodeDO> {

    default PageResult<ComputeNodeDO> selectPage(ComputeNodePageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ComputeNodeDO>()
                .likeIfPresent(ComputeNodeDO::getName, reqVO.getName())
                .likeIfPresent(ComputeNodeDO::getHost, reqVO.getHost())
                .eqIfPresent(ComputeNodeDO::getStatus, reqVO.getStatus())
                .eqIfPresent(ComputeNodeDO::getNodeRole, reqVO.getNodeRole())
                .eqIfPresent(ComputeNodeDO::getRegion, reqVO.getRegion())
                .eqIfPresent(ComputeNodeDO::getControlPlaneId, reqVO.getControlPlaneId())
                .orderByDesc(ComputeNodeDO::getUpdateTime));
    }

    default ComputeNodeDO selectByHost(String host) {
        return selectOne(ComputeNodeDO::getHost, host);
    }

    default ComputeNodeDO selectPlatformNode() {
        return selectList().stream()
                .filter(node -> node.getCapabilities() != null
                        && Boolean.TRUE.equals(node.getCapabilities().get("platform")))
                .findFirst()
                .orElse(null);
    }

}
