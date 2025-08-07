package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.*;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Set;

@Mapper
public interface GroupMapper extends BaseMapperX<Group> {

    /**
     * 添加分组信息
     *
     * @param group 分组对象，包含设备ID、名称、父ID等属性
     * @return 操作影响的行数
     */
    int add(Group group);

    /**
     * 添加业务分组信息
     *
     * @param group 业务分组对象，包含设备ID、名称等属性（无需父节点信息）
     * @return 操作影响的行数
     */
    int addBusinessGroup(Group group);

    /**
     * 根据ID删除分组
     *
     * @param id 分组ID
     * @return 操作影响的行数
     */
    int delete(@Param("id") int id);

    /**
     * 更新分组信息
     *
     * @param group 分组对象，包含待更新的字段
     * @return 操作影响的行数
     */
    int update(Group group);

    /**
     * 查询分组列表（支持条件过滤）
     *
     * @param query        模糊查询关键字（匹配设备ID或名称）
     * @param parentId     父设备ID（可选）
     * @param businessGroup 业务分组ID（可选）
     * @return 分组对象列表
     */
    List<Group> query(@Param("query") String query, @Param("parentId") String parentId, @Param("businessGroup") String businessGroup);

    /**
     * 获取指定父节点下的子分组列表
     *
     * @param parentId 父节点ID
     * @return 子分组对象列表
     */
    List<Group> getChildren(@Param("parentId") int parentId);

    /**
     * 根据ID查询单个分组
     *
     * @param id 分组ID
     * @return 分组对象
     */
    Group queryOne(@Param("id") int id);

    /**
     * 批量添加分组
     *
     * @param groupList 分组对象列表
     * @return 操作影响的行数
     */
    int batchAdd(List<Group> groupList);

    /**
     * 查询分组树结构数据
     *
     * @param query    模糊查询关键字（可选）
     * @param parentId 父节点ID（为null时查询根节点）
     * @return 分组树结构对象列表
     */
    List<GroupTree> queryForTree(@Param("query") String query, @Param("parentId") Integer parentId);

    /**
     * 根据业务分组ID查询分组树结构
     *
     * @param query         模糊查询关键字（可选）
     * @param businessGroup 业务分组ID
     * @return 分组树结构对象列表
     */
    List<GroupTree> queryForTreeByBusinessGroup(@Param("query") String query,
                                                @Param("businessGroup") String businessGroup);

    /**
     * 查询所有业务分组树结构
     *
     * @param query 模糊查询关键字（可选）
     * @return 业务分组树结构对象列表
     */
    List<GroupTree> queryBusinessGroupForTree(@Param("query") String query);

    /**
     * 根据设备ID和业务分组ID查询分组
     *
     * @param deviceId      设备ID
     * @param businessGroup 业务分组ID
     * @return 分组对象
     */
    Group queryOneByDeviceId(@Param("deviceId") String deviceId, @Param("businessGroup") String businessGroup);

    /**
     * 批量删除分组
     *
     * @param allChildren 待删除的分组对象列表
     * @return 操作影响的行数
     */
    int batchDelete(List<Group> allChildren);

    /**
     * 根据业务分组ID查询业务分组
     *
     * @param businessGroup 业务分组ID
     * @return 业务分组对象
     */
    Group queryBusinessGroup(@Param("businessGroup") String businessGroup);

    /**
     * 根据业务分组ID查询关联的分组列表
     *
     * @param businessGroup 业务分组ID
     * @return 分组对象列表
     */
    List<Group> queryByBusinessGroup(@Param("businessGroup") String businessGroup);

    /**
     * 根据业务分组ID删除所有关联分组
     *
     * @param businessGroup 业务分组ID
     * @return 操作影响的行数
     */
    int deleteByBusinessGroup(@Param("businessGroup") String businessGroup);

    /**
     * 更新指定父节点下所有子节点的业务信息
     *
     * @param parentId 父节点ID
     * @param group    包含新业务信息的对象
     * @return 操作影响的行数
     */
    int updateChild(@Param("parentId") Integer parentId, Group group);

    /**
     * 根据设备ID列表查询分组
     *
     * @param groupList 包含设备ID的分组对象列表
     * @return 匹配的分组对象列表
     */
    List<Group> queryInGroupListByDeviceId(List<Group> groupList);

    /**
     * 根据通道列表查询关联的分组
     *
     * @param channelList 通道对象列表（包含gbParentId和gbBusinessGroupId）
     * @return 匹配的分组对象集合
     */
    Set<Group> queryInChannelList(List<CommonGBChannel> channelList);

    /**
     * 根据父节点ID集合查询分组
     *
     * @param groupSet 包含父节点ID的分组对象集合
     * @return 匹配的分组对象集合
     */
    Set<Group> queryParentInChannelList(Set<Group> groupSet);

    /**
     * 查询指定平台关联的国标通道列表
     *
     * @param platformId 平台ID
     * @return 国标通道对象列表
     */
    List<CommonGBChannel> queryForPlatform(@Param("platformId") Integer platformId);

    /**
     * 查询指定平台未共享的分组（通过通道列表）
     *
     * @param channelList 通道对象列表
     * @param platformId  平台ID
     * @return 未共享的分组对象集合
     */
    Set<Group> queryNotShareGroupForPlatformByChannelList(List<CommonGBChannel> channelList, @Param("platformId") Integer platformId);

    /**
     * 查询指定平台未共享的分组（通过分组集合）
     *
     * @param allGroup   分组对象集合
     * @param platformId 平台ID
     * @return 未共享的分组对象集合
     */
    Set<Group> queryNotShareGroupForPlatformByGroupList(Set<Group> allGroup, @Param("platformId") Integer platformId);

    /**
     * 根据通道列表查询关联的分组
     *
     * @param channelList 通道对象列表
     * @return 匹配的分组对象集合
     */
    Set<Group> queryByChannelList(List<CommonGBChannel> channelList);

    /**
     * 批量更新分组的父节点ID
     *
     * @param groupListForAdd 待更新的分组对象列表
     */
    void updateParentId(List<Group> groupListForAdd);

    /**
     * 批量更新业务分组的父节点ID
     *
     * @param groupListForAdd 待更新的分组对象列表
     */
    void updateParentIdWithBusinessGroup(List<Group> groupListForAdd);

    /**
     * 查询分组关联的平台列表
     *
     * @param groupId 分组ID
     * @return 平台对象列表
     */
    List<Platform> queryForPlatformByGroupId(@Param("groupId") int groupId);

    /**
     * 删除分组与平台的关联关系
     *
     * @param groupId 分组ID
     */
    void deletePlatformGroup(@Param("groupId") int groupId);
}