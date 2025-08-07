package com.basiclab.iot.stream.streamPush.service;

import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.service.bean.StreamPushItemFromRedis;
import com.basiclab.iot.stream.streamPush.bean.StreamPush;
import com.basiclab.iot.stream.vmanager.bean.ResourceBaseInfo;
import com.github.pagehelper.PageInfo;

import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * @author lin
 */
public interface IStreamPushService {

    /**
     * 获取
     */
    PageInfo<StreamPush> getPushList(Integer page, Integer count, String query, Boolean pushing, String mediaServerId);

    List<StreamPush> getPushList(String mediaSererId);

    StreamPush getPush(String app, String streamId);

    boolean stop(StreamPush streamPush);

    /**
     * 停止一路推流
     * @param app 应用名
     * @param stream 流ID
     */
    boolean stopByAppAndStream(String app, String stream);

    /**
     * 新的节点加入
     */
    void zlmServerOnline(MediaServer mediaServer);

    /**
     * 节点离线
     */
    void zlmServerOffline(MediaServer mediaServer);

    /**
     * 批量添加
     */
    void batchAdd(List<StreamPush> streamPushExcelDtoList);


    /**
     * 全部离线
     */
    void allOffline();

    /**
     * 推流离线
     */
    void offline(List<StreamPushItemFromRedis> offlineStreams);

    /**
     * 推流上线
     */
    void online(List<StreamPushItemFromRedis> onlineStreams);

    /**
     * 增加推流
     */
    boolean add(StreamPush stream);

    boolean update(StreamPush stream);

    /**
     * 获取全部的app+Streanm 用于判断推流列表是新增还是修改
     * @return
     */
    List<String> getAllAppAndStream();

    /**
     * 获取统计信息
     * @return
     */
    ResourceBaseInfo getOverview();

    Map<String, StreamPush> getAllAppAndStreamMap();

    Map<String, StreamPush> getAllGBId();

    void deleteByAppAndStream(String app, String stream);

    void updatePushStatus(StreamPush streamPush);

    void batchUpdate(List<StreamPush> streamPushItemForUpdate);

    int delete(int id);

    void batchRemove(Set<Integer> ids);

}
