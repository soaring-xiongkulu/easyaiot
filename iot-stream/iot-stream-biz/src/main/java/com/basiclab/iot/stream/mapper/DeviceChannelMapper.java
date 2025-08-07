package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.common.mybatis.core.mapper.BaseMapperX;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.bean.DeviceAlarm;
import com.basiclab.iot.stream.bean.DeviceChannel;
import com.basiclab.iot.stream.controller.bean.ChannelReduce;
import com.basiclab.iot.stream.service.bean.GPSMsgInfo;
import com.basiclab.iot.stream.web.dto.DeviceChannelExtend;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 用于存储设备通道信息
 */
@Mapper
public interface DeviceChannelMapper extends BaseMapperX<DeviceChannel> {


    /**
     * 添加设备通道信息
     *
     * @param channel 设备通道对象
     * @return 影响的行数
     */
    int add(DeviceChannel channel);

    /**
     * 更新设备通道信息
     *
     * @param channel 设备通道对象
     * @return 影响的行数
     */
    int update(DeviceChannel channel);

    /**
     * 查询设备通道列表
     *
     * @param dataDeviceId    设备ID
     * @param civilCode       行政区划代码
     * @param businessGroupId 业务分组ID
     * @param parentChannelId 父通道ID
     * @param query           查询条件
     * @param hasSubChannel   是否有子通道
     * @param online          是否在线
     * @param channelIds      通道ID列表
     * @return 设备通道列表
     */
    List<DeviceChannel> queryChannels(@Param("dataDeviceId") int dataDeviceId, @Param("civilCode") String civilCode,
                                      @Param("businessGroupId") String businessGroupId, @Param("parentChannelId") String parentChannelId,
                                      @Param("query") String query, @Param("hasSubChannel") Boolean hasSubChannel,
                                      @Param("online") Boolean online, @Param("channelIds") List<String> channelIds);

    /**
     * 根据设备ID查询通道列表
     *
     * @param dataDeviceId 设备ID
     * @return 设备通道列表
     */
    List<DeviceChannel> queryChannelsByDeviceDbId(@Param("dataDeviceId") int dataDeviceId);

    /**
     * 根据设备ID列表查询通道ID列表
     *
     * @param deviceDbIds 设备ID列表
     * @return 通道ID列表
     */
    List<Integer> queryChaneIdListByDeviceDbIds(List<Integer> deviceDbIds);

    /**
     * 根据设备ID清理通道
     *
     * @param dataDeviceId 设备ID
     * @return 影响的行数
     */
    int cleanChannelsByDeviceId(@Param("dataDeviceId") int dataDeviceId);

    /**
     * 根据ID删除通道
     *
     * @param id 通道ID
     * @return 影响的行数
     */
    int del(@Param("id") int id);

    /**
     * 查询带有设备信息的通道列表
     *
     * @param deviceId        设备ID
     * @param parentChannelId 父通道ID
     * @param query           查询条件
     * @param hasSubChannel   是否有子通道
     * @param online          是否在线
     * @param channelIds      通道ID列表
     * @return 设备通道扩展信息列表
     */
    List<DeviceChannelExtend> queryChannelsWithDeviceInfo(@Param("deviceId") String deviceId, @Param("parentChannelId") String parentChannelId,
                                                          @Param("query") String query, @Param("hasSubChannel") Boolean hasSubChannel,
                                                          @Param("online") Boolean online, @Param("channelIds") List<String> channelIds);

    /**
     * 开始播放设置流ID
     *
     * @param channelId 通道ID
     * @param streamId  流ID
     */
    void startPlay(@Param("channelId") Integer channelId, @Param("streamId") String streamId);


    /**
     * 查询所有平台通道列表
     *
     * @param query         查询条件
     * @param online        是否在线
     * @param hasSubChannel 是否有子通道
     * @param platformId    平台ID
     * @param catalogId     目录ID
     * @return 通道精简信息列表
     */
    List<ChannelReduce> queryChannelListInAll(@Param("query") String query, @Param("online") Boolean online,
                                              @Param("hasSubChannel") Boolean hasSubChannel, @Param("platformId") String platformId,
                                              @Param("catalogId") String catalogId);


    /**
     * 设置通道离线状态
     *
     * @param id 通道ID
     */
    void offline(@Param("id") int id);

    /**
     * 批量添加设备通道
     *
     * @param addChannels 设备通道列表
     * @return 影响的行数
     */
    int batchAdd(@Param("addChannels") List<DeviceChannel> addChannels);


    /**
     * 设置通道在线状态
     *
     * @param id 通道ID
     */
    void online(@Param("id") int id);

    /**
     * 批量更新设备通道
     *
     * @param updateChannels 设备通道列表
     * @return 影响的行数
     */
    int batchUpdate(List<DeviceChannel> updateChannels);


    /**
     * 为通知批量更新设备通道
     *
     * @param updateChannels 设备通道列表
     * @return 影响的行数
     */
    int batchUpdateForNotify(List<DeviceChannel> updateChannels);

    /**
     * 更新通道子通道数量
     *
     * @param dataDeviceId 设备ID
     * @param channelId    通道ID
     * @return 影响的行数
     */
    int updateChannelSubCount(@Param("dataDeviceId") int dataDeviceId, @Param("channelId") String channelId);

    /**
     * 更新通道位置信息
     *
     * @param deviceChannel 设备通道对象
     * @return 影响的行数
     */
    int updatePosition(DeviceChannel deviceChannel);

    /**
     * 查询设备所有通道信息用于刷新
     *
     * @param dataDeviceId 设备ID
     * @return 设备通道列表
     */
    List<DeviceChannel> queryAllChannelsForRefresh(@Param("dataDeviceId") int dataDeviceId);

    /**
     * 根据通道设备ID获取设备信息
     *
     * @param channelId 通道ID
     * @return 设备列表
     */
    List<Device> getDeviceByChannelDeviceId(@Param("channelId") String channelId);


    /**
     * 批量删除通道
     *
     * @param deleteChannelList 要删除的通道列表
     * @return 影响的行数
     */
    int batchDel(List<DeviceChannel> deleteChannelList);

    /**
     * 批量更新通道状态
     *
     * @param channels 通道列表
     * @return 影响的行数
     */
    int batchUpdateStatus(List<DeviceChannel> channels);

    /**
     * 获取在线通道数量
     *
     * @return 在线通道数量
     */
    int getOnlineCount();

    /**
     * 获取所有通道数量
     *
     * @return 通道总数
     */
    int getAllChannelCount();

    /**
     * 更新通道流标识
     *
     * @param channel 设备通道对象
     */
    void updateChannelStreamIdentification(DeviceChannel channel);

    /**
     * 更新所有通道的流标识
     *
     * @param streamIdentification 流标识
     */
    void updateAllChannelStreamIdentification(@Param("streamIdentification") String streamIdentification);

    /**
     * 批量更新通道位置信息
     *
     * @param channelList 通道列表
     */
    void batchUpdatePosition(List<DeviceChannel> channelList);

    /**
     * 根据ID获取单个通道信息
     *
     * @param id 通道ID
     * @return 设备通道对象
     */
    DeviceChannel getOne(@Param("id") int id);

    /**
     * 根据ID获取原始通道信息
     *
     * @param id 通道ID
     * @return 设备通道对象
     */
    DeviceChannel getOneForSource(@Param("id") int id);

    /**
     * 根据设备ID和通道ID获取通道信息
     *
     * @param dataDeviceId 设备ID
     * @param channelId    通道ID
     * @return 设备通道对象
     */
    DeviceChannel getOneByDeviceId(@Param("dataDeviceId") int dataDeviceId, @Param("channelId") String channelId);


    /**
     * 根据设备ID和通道ID获取原始通道信息
     *
     * @param dataDeviceId 设备ID
     * @param channelId    通道ID
     * @return 设备通道对象
     */
    DeviceChannel getOneByDeviceIdForSource(@Param("dataDeviceId") int dataDeviceId, @Param("channelId") String channelId);


    /**
     * 停止播放并清空流ID
     *
     * @param channelId 通道ID
     */
    void stopPlayById(@Param("channelId") Integer channelId);

    /**
     * 更改通道音频状态
     *
     * @param channelId 通道ID
     * @param audio     音频状态
     */
    void changeAudio(@Param("channelId") int channelId, @Param("audio") boolean audio);

    /**
     * 批量更新通道GPS信息
     *
     * @param gpsMsgInfoList GPS信息列表
     */
    void updateStreamGPS(List<GPSMsgInfo> gpsMsgInfoList);

    /**
     * 更新通道状态
     *
     * @param channel 设备通道对象
     */
    void updateStatus(DeviceChannel channel);


    /**
     * 为通知更新通道信息
     *
     * @param channel 设备通道对象
     */
    void updateChannelForNotify(DeviceChannel channel);


    /**
     * 根据设备ID和通道ID获取源通道信息
     *
     * @param dataDeviceId 设备ID
     * @param channelId    通道ID
     * @return 设备通道对象
     */
    DeviceChannel getOneBySourceChannelId(@Param("dataDeviceId") int dataDeviceId, @Param("channelId") String channelId);

    /**
     * 根据设备ID设置所有通道离线
     *
     * @param deviceId 设备ID
     */
    void offlineByDeviceId(@Param("deviceId") int deviceId);

}
