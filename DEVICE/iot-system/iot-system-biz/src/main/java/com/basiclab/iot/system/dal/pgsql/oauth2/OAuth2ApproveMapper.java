package com.basiclab.iot.system.dal.pgsql.oauth2;

import com.basiclab.iot.common.core.mapper.BaseMapperX;
import com.basiclab.iot.common.core.query.LambdaQueryWrapperX;
import com.basiclab.iot.system.dal.dataobject.oauth2.OAuth2ApproveDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * OAuth2ApproveMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface OAuth2ApproveMapper extends BaseMapperX<OAuth2ApproveDO> {

    default int update(OAuth2ApproveDO updateObj) {
        return update(updateObj, new LambdaQueryWrapperX<OAuth2ApproveDO>()
                .eq(OAuth2ApproveDO::getUserId, updateObj.getUserId())
                .eq(OAuth2ApproveDO::getUserType, updateObj.getUserType())
                .eq(OAuth2ApproveDO::getClientId, updateObj.getClientId())
                .eq(OAuth2ApproveDO::getScope, updateObj.getScope()));
    }

    default List<OAuth2ApproveDO> selectListByUserIdAndUserTypeAndClientId(Long userId, Integer userType, String clientId) {
        return selectList(new LambdaQueryWrapperX<OAuth2ApproveDO>()
                .eq(OAuth2ApproveDO::getUserId, userId)
                .eq(OAuth2ApproveDO::getUserType, userType)
                .eq(OAuth2ApproveDO::getClientId, clientId));
    }

}
