package com.basiclab.iot.device.dal.mysql.protocol;

import com.basiclab.iot.device.controller.admin.protocol.vo.ProtocolPageReqVO;
import com.basiclab.iot.device.dal.dataobject.protocol.ProtocolDO;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.common.mybatis.core.query.LambdaQueryWrapperX;
import org.apache.ibatis.annotations.Mapper;

/**
 * 协议信息 Mapper
 *
 * @author BasicLab
 */
@Mapper
public interface ProtocolMapper extends BaseMapperX<ProtocolDO> {

    default PageResult<ProtocolDO> selectPage(ProtocolPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ProtocolDO>()
                .eqIfPresent(ProtocolDO::getAppId, reqVO.getAppId())
                .eqIfPresent(ProtocolDO::getPid, reqVO.getPid())
                .likeIfPresent(ProtocolDO::getProtocolName, reqVO.getProtocolName())
                .eqIfPresent(ProtocolDO::getProtocolCode, reqVO.getProtocolCode())
                .eqIfPresent(ProtocolDO::getProtocolVersion, reqVO.getProtocolVersion())
                .eqIfPresent(ProtocolDO::getProtocolType, reqVO.getProtocolType())
                .eqIfPresent(ProtocolDO::getProtocolVoice, reqVO.getProtocolVoice())
                .likeIfPresent(ProtocolDO::getClassName, reqVO.getClassName())
                .eqIfPresent(ProtocolDO::getFilePath, reqVO.getFilePath())
                .eqIfPresent(ProtocolDO::getContent, reqVO.getContent())
                .eqIfPresent(ProtocolDO::getStatus, reqVO.getStatus())
                .eqIfPresent(ProtocolDO::getCreateBy, reqVO.getCreateBy())
                .betweenIfPresent(ProtocolDO::getCreateTime, reqVO.getCreateTime())
                .eqIfPresent(ProtocolDO::getUpdateBy, reqVO.getUpdateBy())
                .eqIfPresent(ProtocolDO::getRemark, reqVO.getRemark())
                .orderByDesc(ProtocolDO::getId));
    }

}