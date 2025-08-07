package com.basiclab.iot.stream.service.redisMsg;

import com.basiclab.iot.stream.common.InviteSessionType;
import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.bean.RecordInfo;
import com.basiclab.iot.stream.service.bean.DownloadFileInfo;
import com.basiclab.iot.stream.service.bean.ErrorCallback;
import com.basiclab.iot.stream.vmanager.bean.AudioBroadcastResult;

public interface IRedisRpcPlayService {


    void play(String serverId, Integer channelId, ErrorCallback<StreamInfo> callback);

    void stop(String serverId, InviteSessionType type, int channelId, String stream);

    void playback(String serverId, Integer channelId, String startTime, String endTime, ErrorCallback<StreamInfo> callback);

    void download(String serverId, Integer channelId, String startTime, String endTime, int downloadSpeed, ErrorCallback<StreamInfo> callback);

    void queryRecordInfo(String serverId, Integer channelId, String startTime, String endTime, ErrorCallback<RecordInfo> callback);

    void pauseRtp(String serverId, String streamId);

    void resumeRtp(String serverId, String streamId);

    String frontEndCommand(String serverId, Integer channelId, int cmdCode, int parameter1, int parameter2, int combindCode2);

    void playPush(String serverId, Integer id, ErrorCallback<StreamInfo> callback);

    StreamInfo playProxy(String serverId, int id);

    void stopProxy(String serverId, int id);

    DownloadFileInfo getRecordPlayUrl(String serverId, Integer recordId);


    AudioBroadcastResult audioBroadcast(String serverId, String deviceId, String channelDeviceId, Boolean broadcastMode);
}
