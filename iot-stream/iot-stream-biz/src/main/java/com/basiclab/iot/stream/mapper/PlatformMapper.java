package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.bean.Platform;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 上级平台数据访问接口
 */
@Mapper
@Repository
public interface PlatformMapper {

    /**
     * 添加上级平台信息
     *
     * @param parentPlatform 平台对象，包含所有配置属性
     * @return 操作影响的行数
     */
    int add(Platform parentPlatform);

    /**
     * 更新上级平台信息
     *
     * @param parentPlatform 平台对象，包含所有待更新的属性
     * @return 操作影响的行数
     */
    int update(Platform parentPlatform);

    /**
     * 根据ID删除平台
     *
     * @param id 平台ID
     * @return 操作影响的行数
     */
    int delete(@Param("id") Integer id);

    /**
     * 查询平台列表（支持模糊查询）
     *
     * @param query 查询关键字（可空）
     * @return 平台对象列表（包含通道计数）
     */
    List<Platform> queryList(@Param("query") String query);

    /**
     * 根据服务ID和启用状态查询平台列表
     *
     * @param serverId 服务ID
     * @param enable   是否启用
     * @return 符合条件的平台列表
     */
    List<Platform> queryEnableParentPlatformListByServerId(@Param("serverId") String serverId, @Param("enable") boolean enable);

    /**
     * 查询启用状态且作为消息通道的平台列表
     *
     * @return 符合条件的平台列表
     */
    List<Platform> queryEnablePlatformListWithAsMessageChannel();

    /**
     * 根据平台GBID查询平台信息
     *
     * @param platformGbId 平台GBID
     * @return 平台对象
     */
    Platform getParentPlatByServerGBId(String platformGbId);

    /**
     * 根据ID查询平台详情
     *
     * @param id 平台ID
     * @return 平台对象
     */
    Platform query(int id);

    /**
     * 更新平台在线状态和服务ID
     *
     * @param id       平台ID
     * @param online   是否在线
     * @param serverId 服务ID
     * @return 操作影响的行数
     */
    int updateStatus(@Param("id") int id, @Param("online") boolean online, @Param("serverId") String serverId);

    /**
     * 查询所有启用状态且排除指定服务ID的平台服务ID列表
     *
     * @param serverId 要排除的服务ID
     * @return 服务ID列表
     */
    List<String> queryServerIdsWithEnableAndNotInServer(@Param("serverId") String serverId);

    /**
     * 根据服务ID查询平台列表
     *
     * @param serverId 服务ID
     * @return 平台列表
     */
    List<Platform> queryByServerId(@Param("serverId") String serverId);

    /**
     * 查询所有平台信息
     *
     * @return 平台列表
     */
    List<Platform> queryAll();

    /**
     * 查询启用状态且匹配服务ID的平台列表
     *
     * @param serverId 服务ID
     * @return 平台列表
     */
    List<Platform> queryServerIdsWithEnableAndServer(@Param("serverId") String serverId);

    /**
     * 将指定服务ID的所有平台设为离线状态
     *
     * @param serverId 服务ID
     */
    void offlineAll(@Param("serverId") String serverId);
}