package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.common.CivilCodePo;
import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.Region;
import com.basiclab.iot.stream.bean.RegionTree;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;
import java.util.Set;

@Mapper
public interface RegionMapper {

    /**
     * 添加区域信息
     *
     * @param region 区域对象
     */
    void add(Region region);

    /**
     * 根据ID删除区域
     *
     * @param id 区域ID
     * @return 删除成功的记录数
     */
    int delete(@Param("id") int id);

    /**
     * 更新区域信息
     *
     * @param region 区域对象
     * @return 更新成功的记录数
     */
    int update(Region region);

    /**
     * 查询区域列表（支持条件过滤）
     *
     * @param query 模糊查询关键字
     * @param parentId 父设备ID
     * @return 区域对象列表
     */
    List<Region> query(@Param("query") String query, @Param("parentId") String parentId);

    /**
     * 获取指定父节点下的子区域列表
     *
     * @param parentId 父节点ID
     * @return 子区域列表
     */
    List<Region> getChildren(@Param("parentId") Integer parentId);

    /**
     * 根据ID查询单个区域
     *
     * @param id 区域ID
     * @return 区域对象
     */
    Region queryOne(@Param("id") int id);

    /**
     * 获取未初始化的行政区划代码
     *
     * @return 未初始化的行政区划代码列表
     */
    List<String> getUninitializedCivilCode();

    /**
     * 批量查询区域设备ID是否存在
     *
     * @param codes 设备ID集合
     * @return 存在的设备ID列表
     */
    List<String> queryInList(Set<String> codes);

    /**
     * 批量添加区域
     *
     * @param regionList 区域对象列表
     * @return 添加成功的记录数
     */
    int batchAdd(List<Region> regionList);

    /**
     * 查询区域树结构数据
     *
     * @param query 模糊查询关键字
     * @param parentId 父节点ID
     * @return 区域树结构列表
     */
    List<RegionTree> queryForTree(@Param("query") String query, @Param("parentId") Integer parentId);

    /**
     * 批量删除区域
     *
     * @param allChildren 待删除的区域对象列表
     */
    void batchDelete(List<Region> allChildren);

    /**
     * 根据设备ID列表查询区域
     *
     * @param regionList 包含设备ID的区域对象列表
     * @return 匹配的区域列表
     */
    List<Region> queryInRegionListByDeviceId(List<Region> regionList);

    /**
     * 查询平台关联的国标通道区域信息
     *
     * @param platformId 平台ID
     * @return 国标通道列表
     */
    List<CommonGBChannel> queryByPlatform(@Param("platformId") Integer platformId);

    /**
     * 批量更新区域的父节点ID
     *
     * @param regionListForAdd 待更新的区域对象列表
     */
    void updateParentId(List<Region> regionListForAdd);

    /**
     * 更新子区域的父设备ID
     *
     * @param parentId 父节点ID
     * @param parentDeviceId 父设备ID
     */
    void updateChild(@Param("parentId") int parentId, @Param("parentDeviceId") String parentDeviceId);

    /**
     * 根据设备ID查询区域
     *
     * @param deviceId 设备ID
     * @return 区域对象
     */
    Region queryByDeviceId(@Param("deviceId") String deviceId);

    /**
     * 根据父节点ID集合查询区域
     *
     * @param regionSet 包含父节点ID的区域集合
     * @return 匹配的区域集合
     */
    Set<Region> queryParentInChannelList(Set<Region> regionSet);

    /**
     * 根据通道列表查询关联的区域
     *
     * @param channelList 通道对象列表
     * @return 匹配的区域集合
     */
    Set<Region> queryByChannelList(List<CommonGBChannel> channelList);

    /**
     * 查询指定平台未共享的区域（通过通道列表）
     *
     * @param channelList 通道对象列表
     * @param platformId 平台ID
     * @return 未共享的区域集合
     */
    Set<Region> queryNotShareRegionForPlatformByChannelList(List<CommonGBChannel> channelList, @Param("platformId") Integer platformId);

    /**
     * 查询指定平台未共享的区域（通过区域集合）
     *
     * @param allRegion 区域对象集合
     * @param platformId 平台ID
     * @return 未共享的区域集合
     */
    Set<Region> queryNotShareRegionForPlatformByRegionList(Set<Region> allRegion, @Param("platformId") Integer platformId);

    /**
     * 在行政区划代码列表中查询存在的设备ID
     *
     * @param civilCodePoList 行政区划代码对象列表
     * @return 存在的设备ID集合
     */
    Set<String> queryInCivilCodePoList(List<CivilCodePo> civilCodePoList);
}