package com.basiclab.iot.stream.service;

import com.basiclab.iot.stream.common.InviteInfo;
import com.basiclab.iot.stream.common.InviteSessionType;
import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.config.exception.ServiceException;
import com.basiclab.iot.stream.bean.*;
import com.basiclab.iot.stream.controller.bean.AudioBroadcastEvent;
import com.basiclab.iot.stream.media.bean.MediaInfo;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.media.event.media.MediaArrivalEvent;
import com.basiclab.iot.stream.media.event.media.MediaDepartureEvent;
import com.basiclab.iot.stream.media.event.media.MediaNotFoundEvent;
import com.basiclab.iot.stream.service.bean.ErrorCallback;
import com.basiclab.iot.stream.service.bean.SSRCInfo;
import com.basiclab.iot.stream.vmanager.bean.AudioBroadcastResult;
import gov.nist.javax.sip.message.SIPResponse;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;

import javax.sip.InvalidArgumentException;
import javax.sip.SipException;
import javax.sip.header.CallIdHeader;
import java.text.ParseException;

/**
 * 点播处理
 */
public interface IPlayService {

    SSRCInfo play(MediaServer mediaServerItem, String deviceId, String channelId, String ssrc, ErrorCallback<StreamInfo> callback);

    void play(Device device, DeviceChannel channel, ErrorCallback<StreamInfo> callback);

    StreamInfo onPublishHandlerForPlay(MediaServer mediaServerItem, MediaInfo mediaInfo, Device device, DeviceChannel channel);

    MediaServer getNewMediaServerItem(Device device);

    void playBack(Device device, DeviceChannel channel, String startTime, String endTime, ErrorCallback<StreamInfo> callback);
    void zlmServerOffline(MediaServer mediaServer);

    void download(Device device, DeviceChannel channel, String startTime, String endTime, int downloadSpeed, ErrorCallback<StreamInfo> callback);

    StreamInfo getDownLoadInfo(Device device, DeviceChannel channel, String stream);

    void zlmServerOnline(MediaServer mediaServer);

    AudioBroadcastResult audioBroadcast(String deviceId, String channelDeviceId, Boolean broadcastMode);

    boolean audioBroadcastCmd(Device device, DeviceChannel channel, MediaServer mediaServerItem, String app, String stream, int timeout, boolean isFromPlatform, AudioBroadcastEvent event) throws InvalidArgumentException, ParseException, SipException;

    boolean audioBroadcastInUse(Device device, DeviceChannel channel);

    void stopAudioBroadcast(Device device, DeviceChannel channel);

    void pauseRtp(String streamId) throws ServiceException, InvalidArgumentException, ParseException, SipException;

    void resumeRtp(String streamId) throws ServiceException, InvalidArgumentException, ParseException, SipException;

    void startPushStream(SendRtpInfo sendRtpItem, DeviceChannel channel, SIPResponse sipResponse, Platform platform, CallIdHeader callIdHeader);

    void startSendRtpStreamFailHand(SendRtpInfo sendRtpItem, Platform platform, CallIdHeader callIdHeader);

    void talkCmd(Device device, DeviceChannel channel, MediaServer mediaServerItem, String stream, AudioBroadcastEvent event);

    void stopTalk(Device device, DeviceChannel channel, Boolean streamIsReady);

    void getSnap(String deviceId, String channelId, String fileName, ErrorCallback errorCallback);

    void stop(InviteSessionType type, Device device, DeviceChannel channel, String stream);

    void stop(InviteInfo inviteInfo);

    void play(CommonGBChannel channel, Boolean record, ErrorCallback<StreamInfo> callback);

    void stop(InviteSessionType inviteSessionType, CommonGBChannel channel, String stream);

    void playBack(CommonGBChannel channel, Long startTime, Long stopTime, ErrorCallback<StreamInfo> callback);

    void download(CommonGBChannel channel, Long startTime, Long stopTime, Integer downloadSpeed, ErrorCallback<StreamInfo> callback);

    @Async("taskExecutor")
    @EventListener
    void onApplicationEvent(MediaArrivalEvent event);

    @Async("taskExecutor")
    @EventListener
    void onApplicationEvent(MediaDepartureEvent event);

    @Async("taskExecutor")
    @EventListener
    void onApplicationEvent(MediaNotFoundEvent event);



}
