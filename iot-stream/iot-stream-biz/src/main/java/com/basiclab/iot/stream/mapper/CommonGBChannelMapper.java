package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.*;
import com.basiclab.iot.stream.service.bean.GPSMsgInfo;
import com.basiclab.iot.stream.streamPush.bean.StreamPush;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Collection;
import java.util.List;

@Mapper
@Repository
public interface CommonGBChannelMapper extends BaseMapperX<CommonGBChannel> {

    /**
     * 根据设备ID查询GB通道
     *
     * @param gbDeviceId 设备ID
     * @return GB通道实体
     */
    CommonGBChannel queryByDeviceId(@Param("gbDeviceId") String gbDeviceId);

    /**
     * 插入GB通道
     *
     * @param commonGBChannel GB通道实体
     * @return 插入结果
     */
    int insert(CommonGBChannel commonGBChannel);

    /**
     * 根据ID查询GB通道
     *
     * @param gbId GB通道ID
     * @return GB通道实体
     */
    CommonGBChannel queryById(@Param("gbId") int gbId);

    /**
     * 根据ID删除GB通道
     *
     * @param gbId GB通道ID
     */
    void delete(int gbId);

    /**
     * 更新GB通道信息
     *
     * @param commonGBChannel GB通道实体
     * @return 更新结果
     */
    int update(CommonGBChannel commonGBChannel);

    /**
     * 根据ID更新GB通道状态
     *
     * @param gbId   GB通道ID
     * @param status 状态值
     * @return 更新结果
     */
    int updateStatusById(@Param("gbId") int gbId, @Param("status") String status);

    /**
     * 批量更新GB通道状态
     *
     * @param commonGBChannels GB通道列表
     * @param status           状态值
     * @return 更新结果
     */
    int updateStatusForListById(List<CommonGBChannel> commonGBChannels, @Param("status") String status);

    /**
     * 根据状态查询GB通道列表
     *
     * @param commonGBChannelList GB通道列表
     * @param status              状态值
     * @return GB通道列表
     */
    List<CommonGBChannel> queryInListByStatus(List<CommonGBChannel> commonGBChannelList, @Param("status") String status);

    /**
     * 批量插入GB通道
     *
     * @param commonGBChannels GB通道列表
     * @return 插入结果
     */
    int batchAdd(List<CommonGBChannel> commonGBChannels);

    /**
     * 批量更新GB通道状态
     *
     * @param commonGBChannels GB通道列表
     * @return 更新结果
     */
    int updateStatus(List<CommonGBChannel> commonGBChannels);

    /**
     * 重置GB通道信息
     *
     * @param id           GB通道ID
     * @param dataType     数据类型
     * @param dataDeviceId 数据设备ID
     * @param updateTime   更新时间
     */
    void reset(@Param("id") int id, @Param("dataType") Integer dataType, @Param("dataDeviceId") int dataDeviceId, @Param("updateTime") String updateTime);

    /**
     * 根据ID集合查询GB通道列表
     *
     * @param ids ID集合
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByIds(Collection<Integer> ids);

    /**
     * 批量删除GB通道
     *
     * @param channelListInDb GB通道列表
     */
    void batchDelete(List<CommonGBChannel> channelListInDb);

    /**
     * 根据公民代码查询GB通道列表
     *
     * @param query     查询条件
     * @param online    是否在线
     * @param dataType  数据类型
     * @param civilCode 公民代码
     * @return GB通道列表
     */
    List<CommonGBChannel> queryListByCivilCode(@Param("query") String query, @Param("online") Boolean online,
                                               @Param("dataType") Integer dataType, @Param("civilCode") String civilCode);

    /**
     * 根据父ID查询GB通道列表
     *
     * @param query         查询条件
     * @param online        是否在线
     * @param dataType      数据类型
     * @param groupDeviceId 组设备ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryListByParentId(@Param("query") String query, @Param("online") Boolean online,
                                              @Param("dataType") Integer dataType, @Param("groupDeviceId") String groupDeviceId);

    /**
     * 根据公民代码查询区域树结构
     *
     * @param query          查询条件
     * @param parentDeviceId 父设备ID
     * @return 区域树结构列表
     */
    List<RegionTree> queryForRegionTreeByCivilCode(@Param("query") String query, @Param("parentDeviceId") String parentDeviceId);

    /**
     * 移除GB通道的公民代码
     *
     * @param allChildren 所有子设备列表
     * @return 更新结果
     */
    int removeCivilCode(List<Region> allChildren);

    /**
     * 更新GB通道的公民代码
     *
     * @param civilCode   公民代码
     * @param channelList GB通道列表
     * @return 更新结果
     */
    int updateRegion(@Param("civilCode") String civilCode, @Param("channelList") List<CommonGBChannel> channelList);

    /**
     * 根据公民代码或ID集合查询GB通道列表
     *
     * @param civilCode 公民代码
     * @param ids       ID集合
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByIdsOrCivilCode(@Param("civilCode") String civilCode, @Param("ids") List<Integer> ids);

    /**
     * 根据GB通道列表移除公民代码
     *
     * @param channelList GB通道列表
     * @return 更新结果
     */
    int removeCivilCodeByChannels(List<CommonGBChannel> channelList);

    /**
     * 根据ID集合移除公民代码
     *
     * @param channelIdList ID集合
     * @return 更新结果
     */
    int removeCivilCodeByChannelIds(List<Integer> channelIdList);

    /**
     * 根据公民代码查询GB通道列表
     *
     * @param civilCode 公民代码
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByCivilCode(@Param("civilCode") String civilCode);

    /**
     * 根据GB设备ID列表查询GB通道列表
     *
     * @param dataType  数据类型
     * @param deviceIds 设备ID列表
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByGbDeviceIds(@Param("dataType") Integer dataType, List<Integer> deviceIds);

    /**
     * 根据GB设备ID列表查询ID集合
     *
     * @param dataType  数据类型
     * @param deviceIds 设备ID列表
     * @return ID集合
     */
    List<Integer> queryByGbDeviceIdsForIds(@Param("dataType") Integer dataType, List<Integer> deviceIds);

    /**
     * 根据组列表查询GB通道列表
     *
     * @param groupList 组列表
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByGroupList(List<Group> groupList);

    /**
     * 根据GB通道列表移除父ID和业务组ID
     *
     * @param channelList GB通道列表
     * @return 更新结果
     */
    int removeParentIdByChannels(List<CommonGBChannel> channelList);

    /**
     * 根据业务组查询GB通道列表
     *
     * @param businessGroup 业务组
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByBusinessGroup(@Param("businessGroup") String businessGroup);

    /**
     * 根据父ID查询GB通道列表
     *
     * @param parentId 父ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryByParentId(@Param("parentId") String parentId);

    /**
     * 根据业务组更新GB通道列表的业务组ID
     *
     * @param businessGroup 业务组
     * @param channelList   GB通道列表
     * @return 更新结果
     */
    int updateBusinessGroupByChannelList(@Param("businessGroup") String businessGroup, List<CommonGBChannel> channelList);

    /**
     * 根据父ID更新GB通道列表的父ID
     *
     * @param parentId    父ID
     * @param channelList GB通道列表
     * @return 更新结果
     */
    int updateParentIdByChannelList(@Param("parentId") String parentId, List<CommonGBChannel> channelList);

    /**
     * 根据父ID查询组树结构
     *
     * @param query  查询条件
     * @param parent 父ID
     * @return 组树结构列表
     */
    List<GroupTree> queryForGroupTreeByParentId(@Param("query") String query, @Param("parent") String parent);

    /**
     * 根据父ID和业务组更新GB通道列表的父ID和业务组ID
     *
     * @param parentId      父ID
     * @param businessGroup 业务组
     * @param channelList   GB通道列表
     * @return 更新结果
     */
    int updateGroup(@Param("parentId") String parentId, @Param("businessGroup") String businessGroup,
                    List<CommonGBChannel> channelList);

    /**
     * 批量更新GB通道信息
     *
     * @param commonGBChannels GB通道列表
     * @return 更新结果
     */
    int batchUpdate(List<CommonGBChannel> commonGBChannels);

    /**
     * 根据平台ID查询GB通道列表
     *
     * @param platformId 平台ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryWithPlatform(@Param("platformId") Integer platformId);

    /**
     * 根据父ID和平台ID查询共享GB通道列表
     *
     * @param parentId   父ID
     * @param platformId 平台ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryShareChannelByParentId(@Param("parentId") String parentId, @Param("platformId") Integer platformId);

    /**
     * 根据公民代码和平台ID查询共享GB通道列表
     *
     * @param civilCode  公民代码
     * @param platformId 平台ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryShareChannelByCivilCode(@Param("civilCode") String civilCode, @Param("platformId") Integer platformId);

    /**
     * 根据GB通道列表更新公民代码
     *
     * @param civilCode   公民代码
     * @param channelList GB通道列表
     * @return 更新结果
     */
    int updateCivilCodeByChannelList(@Param("civilCode") String civilCode, List<CommonGBChannel> channelList);

    /**
     * 根据数据类型和流推送列表查询GB通道列表
     *
     * @param dataType       数据类型
     * @param streamPushList 流推送列表
     * @return GB通道列表
     */
    List<CommonGBChannel> queryListByStreamPushList(@Param("dataType") Integer dataType, List<StreamPush> streamPushList);

    /**
     * 根据设备ID列表更新GPS信息
     *
     * @param gpsMsgInfoList GPS信息列表
     */
    void updateGpsByDeviceId(List<GPSMsgInfo> gpsMsgInfoList);

    /**
     * 查询GB通道列表
     *
     * @param query         查询条件
     * @param online        是否在线
     * @param hasRecordPlan 是否有录像计划
     * @param dataType      数据类型
     * @return GB通道列表
     */
    List<CommonGBChannel> queryList(@Param("query") String query, @Param("online") Boolean online,
                                    @Param("hasRecordPlan") Boolean hasRecordPlan, @Param("dataType") Integer dataType);

    /**
     * 移除GB通道的录像计划ID
     *
     * @param channelIds 通道ID列表
     */
    void removeRecordPlan(List<Integer> channelIds);

    /**
     * 添加GB通道的录像计划ID
     *
     * @param channelIds 通道ID列表
     * @param planId     录像计划ID
     */
    void addRecordPlan(List<Integer> channelIds, @Param("planId") Integer planId);

    /**
     * 为所有GB通道添加录像计划ID
     *
     * @param planId 录像计划ID
     */
    void addRecordPlanForAll(@Param("planId") Integer planId);

    /**
     * 根据录像计划ID移除GB通道的录像计划ID
     *
     * @param planId 录像计划ID
     */
    void removeRecordPlanByPlanId(@Param("planId") Integer planId);

    /**
     * 查询GB通道列表（用于Web端录像计划）
     *
     * @param planId   录像计划ID
     * @param query    查询条件
     * @param dataType 数据类型
     * @param online   是否在线
     * @param hasLink  是否有链接
     * @return GB通道列表
     */
    List<CommonGBChannel> queryForRecordPlanForWebList(@Param("planId") Integer planId, @Param("query") String query,
                                                       @Param("dataType") Integer dataType, @Param("online") Boolean online,
                                                       @Param("hasLink") Boolean hasLink);

    /**
     * 根据数据类型和数据设备ID查询GB通道
     *
     * @param dataType     数据类型
     * @param dataDeviceId 数据设备ID
     * @return GB通道实体
     */
    CommonGBChannel queryByDataId(@Param("dataType") Integer dataType, @Param("dataDeviceId") Integer dataDeviceId);

    /**
     * 根据公民代码查询异常GB通道列表
     *
     * @param query    查询条件
     * @param online   是否在线
     * @param dataType 数据类型
     * @return GB通道列表
     */
    List<CommonGBChannel> queryListByCivilCodeForUnusual(@Param("query") String query, @Param("online") Boolean online, @Param("dataType") Integer dataType);

    /**
     * 查询所有异常的公民代码
     *
     * @return 公民代码列表
     */
    List<Integer> queryAllForUnusualCivilCode();

    /**
     * 根据父ID查询异常GB通道列表
     *
     * @param query    查询条件
     * @param online   是否在线
     * @param dataType 数据类型
     * @return GB通道列表
     */
    List<CommonGBChannel> queryListByParentForUnusual(@Param("query") String query, @Param("online") Boolean online, @Param("dataType") Integer dataType);

    /**
     * 查询所有异常的父ID
     *
     * @return 父ID列表
     */
    List<Integer> queryAllForUnusualParent();

    /**
     * 根据ID集合移除GB通道的父ID和业务组ID
     *
     * @param channelIdsForClear ID集合
     */
    void removeParentIdByChannelIds(List<Integer> channelIdsForClear);

    /**
     * 查询在线的GB通道列表（根据GB设备ID）
     *
     * @param deviceId GB设备ID
     * @return GB通道列表
     */
    List<CommonGBChannel> queryOnlineListsByGbDeviceId(@Param("deviceId") int deviceId);
}