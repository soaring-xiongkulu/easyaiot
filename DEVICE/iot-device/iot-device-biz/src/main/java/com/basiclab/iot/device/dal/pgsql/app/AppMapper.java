package com.basiclab.iot.device.dal.pgsql.app;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.basiclab.iot.device.dal.dataobject.AppDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * AppMapper
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Mapper
public interface AppMapper extends BaseMapper<AppDO> {

    /**
     * 根据AppId查询应用信息
     *
     * @param appId 应用ID
     * @return 应用信息
     */
    AppDO selectByAppId(@Param("appId") String appId);

    /**
     * 根据AppKey查询应用信息
     *
     * @param appKey 应用密钥
     * @return 应用信息
     */
    AppDO selectByAppKey(@Param("appKey") String appKey);

    /**
     * 根据AppId和AppKey查询应用信息
     *
     * @param appId  应用ID
     * @param appKey 应用密钥
     * @return 应用信息
     */
    AppDO selectByAppIdAndAppKey(@Param("appId") String appId, @Param("appKey") String appKey);
}

