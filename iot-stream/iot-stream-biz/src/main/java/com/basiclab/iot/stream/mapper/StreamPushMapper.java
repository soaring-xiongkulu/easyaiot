package com.basiclab.iot.stream.mapper;

import com.basiclab.iot.stream.common.enums.ChannelDataType;
import com.basiclab.iot.stream.service.bean.StreamPushItemFromRedis;
import com.basiclab.iot.stream.streamPush.bean.StreamPush;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;
import java.util.Set;

@Mapper
@Repository
public interface StreamPushMapper {

    Integer dataType = ChannelDataType.GB28181.value;

    /**
     * 添加流推送记录
     *
     * @param streamPushItem 流推送记录实体
     * @return 插入结果
     */
    int add(StreamPush streamPushItem);

    /**
     * 更新流推送记录
     *
     * @param streamPushItem 流推送记录实体
     * @return 更新结果
     */
    int update(StreamPush streamPushItem);

    /**
     * 根据ID删除流推送记录
     *
     * @param id 流推送记录ID
     * @return 删除结果
     */
    int del(@Param("id") int id);

    /**
     * 查询所有流推送记录
     *
     * @param query 查询条件
     * @param pushing 是否正在推送
     * @param mediaServerId 媒体服务器ID
     * @return 流推送记录列表
     */
    List<StreamPush> selectAll(@Param("query") String query, @Param("pushing") Boolean pushing, @Param("mediaServerId") String mediaServerId);

    /**
     * 根据应用和流查询流推送记录
     *
     * @param app 应用标识
     * @param stream 流标识
     * @return 流推送记录实体
     */
    StreamPush selectByAppAndStream(@Param("app") String app, @Param("stream") String stream);

    /**
     * 批量添加流推送记录
     *
     * @param streamPushItems 流推送记录列表
     * @return 插入结果
     */
    int addAll(List<StreamPush> streamPushItems);

    /**
     * 根据媒体服务器ID查询所有流推送记录
     *
     * @param mediaServerId 媒体服务器ID
     * @return 流推送记录列表
     */
    List<StreamPush> selectAllByMediaServerId(String mediaServerId);

    /**
     * 根据媒体服务器ID查询没有GB ID的流推送记录
     *
     * @param mediaServerId 媒体服务器ID
     * @return 流推送记录列表
     */
    List<StreamPush> selectAllByMediaServerIdWithOutGbID(String mediaServerId);

    /**
     * 更新流推送记录的推送状态
     *
     * @param streamPush 流推送记录实体
     * @return 更新结果
     */
    int updatePushStatus(StreamPush streamPush);

    /**
     * 根据离线流列表查询流推送记录
     *
     * @param offlineStreams 离线流列表
     * @return 流推送记录列表
     */
    List<StreamPush> getListInList(List<StreamPushItemFromRedis> offlineStreams);

    /**
     * 查询所有应用和流的组合
     *
     * @return 应用和流的组合列表
     */
    List<String> getAllAppAndStream();

    /**
     * 获取所有流推送记录的数量
     *
     * @return 流推送记录数量
     */
    int getAllCount();

    /**
     * 获取正在推送的流推送记录的数量
     *
     * @param usePushingAsStatus 是否使用推送状态作为条件
     * @return 正在推送的流推送记录数量
     */
    int getAllPushing(Boolean usePushingAsStatus);

    /**
     * 查询所有应用和流的组合，并映射为Map
     *
     * @return 应用和流的组合Map
     */
    Map<String, StreamPush> getAllAppAndStreamMap();

    /**
     * 查询所有GB ID，并映射为Map
     *
     * @return GB ID的Map
     */
    Map<String, StreamPush> getAllGBId();

    /**
     * 根据ID查询流推送记录
     *
     * @param id 流推送记录ID
     * @return 流推送记录实体
     */
    StreamPush queryOne(@Param("id") int id);

    /**
     * 根据ID集合查询流推送记录
     *
     * @param ids ID集合
     * @return 流推送记录列表
     */
    List<StreamPush> selectInSet(Set<Integer> ids);

    /**
     * 批量删除流推送记录
     *
     * @param streamPushList 流推送记录列表
     */
    void batchDel(List<StreamPush> streamPushList);

    /**
     * 批量更新流推送记录
     *
     * @param streamPushItemForUpdate 流推送记录更新列表
     * @return 更新结果
     */
    int batchUpdate(List<StreamPush> streamPushItemForUpdate);
}