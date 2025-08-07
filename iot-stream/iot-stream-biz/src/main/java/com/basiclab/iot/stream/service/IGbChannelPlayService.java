package com.basiclab.iot.stream.service;

import com.basiclab.iot.stream.common.InviteSessionType;
import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.InviteMessageInfo;
import com.basiclab.iot.stream.bean.Platform;
import com.basiclab.iot.stream.service.bean.ErrorCallback;

public interface IGbChannelPlayService {

    void start(CommonGBChannel channel, InviteMessageInfo inviteInfo, Platform platform, ErrorCallback<StreamInfo> callback);

    void stopPlay(InviteSessionType type, CommonGBChannel channel, String stream);

    void play(CommonGBChannel channel, Platform platform, Boolean record, ErrorCallback<StreamInfo> callback);

    void playGbDeviceChannel(CommonGBChannel channel, Boolean record, ErrorCallback<StreamInfo> callback);

    void stopPlayDeviceChannel(InviteSessionType type, CommonGBChannel channel, String stream);

    void playProxy(CommonGBChannel channel, Boolean record, ErrorCallback<StreamInfo> callback);

    void stopPlayProxy(CommonGBChannel channel);

    void playPush(CommonGBChannel channel, String platformDeviceId, String platformName, ErrorCallback<StreamInfo> callback);

    void  stopPlayPush(CommonGBChannel channel);

    void pauseRtp(String streamId);

    void resumeRtp(String streamId);
}
