package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.*;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.List;
import java.util.Set;

@Mapper
@Repository
public interface PlatformChannelMapper extends BaseMapperX<Platform> {

    /**
     * 批量添加平台与通道的关联关系
     *
     * @param platformId  平台ID
     * @param channelList 要关联的通道列表
     * @return 添加成功的记录数
     */
    int addChannels(@Param("platformId") Integer platformId, @Param("channelList") List<CommonGBChannel> channelList);

    /**
     * 根据设备ID删除关联的通道
     *
     * @param deviceId 设备ID
     * @return 删除成功的记录数
     */
    int delChannelForDeviceId(String deviceId);

    /**
     * 根据平台ID和通道ID查询关联的设备
     *
     * @param platformId 平台ID
     * @param channelId  通道ID
     * @return 关联的设备列表
     */
    List<Device> queryDeviceByPlatformIdAndChannelId(@Param("platformId") String platformId, @Param("channelId") String channelId);

    /**
     * 根据通道ID和平台GBID列表查询平台信息
     *
     * @param channelId 通道ID
     * @param platforms 平台GBID列表
     * @return 符合条件的平台列表
     */
    List<Platform> queryPlatFormListForGBWithGBId(@Param("channelId") Integer channelId, List<String> platforms);

    /**
     * 根据平台ID和通道ID查询设备详细信息
     *
     * @param platformId 平台ID
     * @param channelId  通道ID
     * @return 设备信息列表
     */
    List<Device> queryDeviceInfoByPlatformIdAndChannelId(@Param("platformId") String platformId, @Param("channelId") String channelId);

    /**
     * 根据通道ID查询关联的上级平台
     *
     * @param channelId 通道ID
     * @return 关联的平台列表
     */
    List<Platform> queryParentPlatformByChannelId(@Param("channelId") String channelId);

    /**
     * 查询平台通道的Web列表数据
     *
     * @param platformId 平台ID
     * @param query      查询关键字
     * @param dataType   数据类型
     * @param online     在线状态
     * @param hasShare   是否已共享
     * @return 平台通道列表
     */
    List<PlatformChannel> queryForPlatformForWebList(@Param("platformId") Integer platformId, @Param("query") String query,
                                                     @Param("dataType") Integer dataType, @Param("online") Boolean online,
                                                     @Param("hasShare") Boolean hasShare);

    /**
     * 根据平台ID和通道设备ID查询通道详情
     *
     * @param platformId      平台ID
     * @param channelDeviceId 通道设备ID
     * @return 通道详细信息列表
     */
    List<CommonGBChannel> queryOneWithPlatform(@Param("platformId") Integer platformId, @Param("channelDeviceId") String channelDeviceId);

    /**
     * 查询指定平台未共享的通道列表
     *
     * @param platformId 平台ID
     * @param channelIds 通道ID列表
     * @return 未共享的通道列表
     */
    List<CommonGBChannel> queryNotShare(@Param("platformId") Integer platformId, List<Integer> channelIds);

    /**
     * 查询指定平台已共享的通道列表
     *
     * @param platformId 平台ID
     * @param channelIds 通道ID列表
     * @return 已共享的通道列表
     */
    List<CommonGBChannel> queryShare(@Param("platformId") Integer platformId, List<Integer> channelIds);

    /**
     * 删除指定平台的通道关联
     *
     * @param platformId  平台ID
     * @param channelList 要删除的通道列表
     * @return 删除的记录数
     */
    int removeChannelsWithPlatform(@Param("platformId") Integer platformId, List<CommonGBChannel> channelList);

    /**
     * 删除通道关联
     *
     * @param channelList 要删除的通道列表
     * @return 删除的记录数
     */
    int removeChannels(List<CommonGBChannel> channelList);

    /**
     * 添加平台与分组的关联
     *
     * @param groupListNotShare 要关联的分组列表
     * @param platformId        平台ID
     * @return 添加的记录数
     */
    int addPlatformGroup(Collection<Group> groupListNotShare, @Param("platformId") Integer platformId);

    /**
     * 添加平台与区域的关联
     *
     * @param regionListNotShare 要关联的区域列表
     * @param platformId         平台ID
     * @return 添加的记录数
     */
    int addPlatformRegion(List<Region> regionListNotShare, @Param("platformId") Integer platformId);

    /**
     * 删除平台与分组的关联
     *
     * @param groupList  要删除的分组列表
     * @param platformId 平台ID
     * @return 删除的记录数
     */
    int removePlatformGroup(List<Group> groupList, @Param("platformId") Integer platformId);

    /**
     * 根据ID删除平台分组关联
     *
     * @param id         分组ID
     * @param platformId 平台ID
     */
    void removePlatformGroupById(@Param("id") int id, @Param("platformId") Integer platformId);

    /**
     * 根据ID删除平台区域关联
     *
     * @param id         区域ID
     * @param platformId 平台ID
     */
    void removePlatformRegionById(@Param("id") int id, @Param("platformId") Integer platformId);

    /**
     * 查询指定父节点下已共享的子分组
     *
     * @param parentId   父节点ID
     * @param platformId 平台ID
     * @return 已共享的子分组集合
     */
    Set<Group> queryShareChildrenGroup(@Param("parentId") Integer parentId, @Param("platformId") Integer platformId);

    /**
     * 查询指定父节点下已共享的子区域
     *
     * @param parentId   父节点ID
     * @param platformId 平台ID
     * @return 已共享的子区域集合
     */
    Set<Region> queryShareChildrenRegion(@Param("parentId") String parentId, @Param("platformId") Integer platformId);

    /**
     * 根据分组集合查询已共享的父分组
     *
     * @param groupSet   分组集合
     * @param platformId 平台ID
     * @return 已共享的父分组集合
     */
    Set<Group> queryShareParentGroupByGroupSet(Set<Group> groupSet, @Param("platformId") Integer platformId);

    /**
     * 根据区域集合查询已共享的父区域
     *
     * @param regionSet  区域集合
     * @param platformId 平台ID
     * @return 已共享的父区域集合
     */
    Set<Region> queryShareParentRegionByRegionSet(Set<Region> regionSet, @Param("platformId") Integer platformId);

    /**
     * 根据通道ID列表查询关联的平台
     *
     * @param ids 通道ID集合
     * @return 关联的平台列表
     */
    List<Platform> queryPlatFormListByChannelList(Collection<Integer> ids);

    /**
     * 根据通道ID查询关联的平台
     *
     * @param channelId 通道ID
     * @return 关联的平台列表
     */
    List<Platform> queryPlatFormListByChannelId(@Param("channelId") int channelId);

    /**
     * 根据平台ID删除所有通道关联
     *
     * @param platformId 平台ID
     */
    void removeChannelsByPlatformId(@Param("platformId") Integer platformId);

    /**
     * 根据平台ID删除所有分组关联
     *
     * @param platformId 平台ID
     */
    void removePlatformGroupsByPlatformId(@Param("platformId") Integer platformId);

    /**
     * 根据平台ID删除所有区域关联
     *
     * @param platformId 平台ID
     */
    void removePlatformRegionByPlatformId(@Param("platformId") Integer platformId);

    /**
     * 更新自定义通道信息
     *
     * @param channel 包含更新信息的通道对象
     */
    void updateCustomChannel(PlatformChannel channel);

    /**
     * 查询指定平台和GBID的共享通道详情
     *
     * @param platformId 平台ID
     * @param gbId       通道GBID
     * @return 通道详细信息
     */
    CommonGBChannel queryShareChannel(@Param("platformId") int platformId, @Param("gbId") int gbId);

    /**
     * 查询指定平台的共享分组
     *
     * @param platformId 平台ID
     * @return 共享的分组集合
     */
    Set<Group> queryShareGroup(@Param("platformId") Integer platformId);

    /**
     * 查询指定平台的共享区域
     *
     * @param id 平台ID
     * @return 共享的区域集合
     */
    Set<Region> queryShareRegion(Integer id);
}