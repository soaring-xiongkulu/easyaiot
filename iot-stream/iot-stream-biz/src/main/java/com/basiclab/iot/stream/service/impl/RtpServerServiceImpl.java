package com.basiclab.iot.stream.service.impl;

import com.basiclab.iot.stream.config.DynamicTask;
import com.basiclab.iot.stream.config.UserSetting;
import com.basiclab.iot.stream.bean.OpenRTPServerResult;
import com.basiclab.iot.stream.session.SSRCFactory;
import com.basiclab.iot.stream.session.SipInviteSessionManager;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.media.event.hook.Hook;
import com.basiclab.iot.stream.media.event.hook.HookSubscribe;
import com.basiclab.iot.stream.media.event.hook.HookType;
import com.basiclab.iot.stream.media.event.media.MediaArrivalEvent;
import com.basiclab.iot.stream.media.event.media.MediaDepartureEvent;
import com.basiclab.iot.stream.media.service.IMediaServerService;
import com.basiclab.iot.stream.service.IReceiveRtpServerService;
import com.basiclab.iot.stream.service.bean.ErrorCallback;
import com.basiclab.iot.stream.service.bean.InviteErrorCode;
import com.basiclab.iot.stream.service.bean.RTPServerParam;
import com.basiclab.iot.stream.service.bean.SSRCInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Slf4j
@Service
public class RtpServerServiceImpl implements IReceiveRtpServerService {

    @Autowired
    private IMediaServerService mediaServerService;

    @Autowired
    private DynamicTask dynamicTask;

    @Autowired
    private SSRCFactory ssrcFactory;

    @Autowired
    private UserSetting userSetting;

    @Autowired
    private HookSubscribe subscribe;

    @Autowired
    private SipInviteSessionManager sessionManager;

    /**
     * 流到来的处理
     */
    @Async("taskExecutor")
    @EventListener
    public void onApplicationEvent(MediaArrivalEvent event) {

    }

    /**
     * 流离开的处理
     */
    @Async("taskExecutor")
    @EventListener
    public void onApplicationEvent(MediaDepartureEvent event) {

    }

    @Override
    public SSRCInfo openRTPServer(RTPServerParam rtpServerParam, ErrorCallback<OpenRTPServerResult> callback) {
        if (callback == null) {
            log.warn("[开启RTP收流] 失败，回调为NULL");
            return null;
        }
        if (rtpServerParam.getMediaServerItem() == null) {
            log.warn("[开启RTP收流] 失败，媒体节点为NULL");
            return null;
        }

        // 获取mediaServer可用的ssrc
        final String ssrc;
        if (rtpServerParam.getPresetSsrc() != null) {
            ssrc = rtpServerParam.getPresetSsrc();
        }else {
            if (rtpServerParam.isPlayback()) {
                ssrc = ssrcFactory.getPlayBackSsrc(rtpServerParam.getMediaServerItem().getId());
            }else {
                ssrc = ssrcFactory.getPlaySsrc(rtpServerParam.getMediaServerItem().getId());
            }
        }
        final String streamId;
        if (rtpServerParam.getStreamId() == null) {
            streamId = String.format("%08x", Long.parseLong(ssrc)).toUpperCase();
        }else {
            streamId = rtpServerParam.getStreamId();
        }
        if (rtpServerParam.isSsrcCheck() && rtpServerParam.getTcpMode() > 0) {
            // 目前zlm不支持 tcp模式更新ssrc，暂时关闭ssrc校验
            log.warn("[openRTPServer] 平台对接时下级可能自定义ssrc，但是tcp模式zlm收流目前无法更新ssrc，可能收流超时，此时请使用udp收流或者关闭ssrc校验");
        }
        int rtpServerPort;
        if (rtpServerParam.getMediaServerItem().isRtpEnable()) {
            rtpServerPort = mediaServerService.createRTPServer(rtpServerParam.getMediaServerItem(), streamId,
                    rtpServerParam.isSsrcCheck() ? Long.parseLong(ssrc) : 0, rtpServerParam.getPort(), rtpServerParam.isOnlyAuto(),
                    rtpServerParam.isDisableAudio(), rtpServerParam.isReUsePort(), rtpServerParam.getTcpMode());
        } else {
            rtpServerPort = rtpServerParam.getMediaServerItem().getRtpProxyPort();
        }
        if (rtpServerPort == 0) {
            callback.run(InviteErrorCode.ERROR_FOR_RESOURCE_EXHAUSTION.getCode(), "开启RTPServer失败", null);
            // 释放ssrc
            if (rtpServerParam.getPresetSsrc() == null) {
                ssrcFactory.releaseSsrc(rtpServerParam.getMediaServerItem().getId(), ssrc);
            }
            return null;
        }

        // 设置流超时的定时任务
        String timeOutTaskKey = UUID.randomUUID().toString();

        SSRCInfo ssrcInfo = new SSRCInfo(rtpServerPort, ssrc, "rtp", streamId, timeOutTaskKey);
        OpenRTPServerResult openRTPServerResult = new OpenRTPServerResult();
        openRTPServerResult.setSsrcInfo(ssrcInfo);

        Hook rtpHook = Hook.getInstance(HookType.on_media_arrival, ssrcInfo.getApp(), streamId, rtpServerParam.getMediaServerItem().getId());
        dynamicTask.startDelay(timeOutTaskKey, () -> {
            // 收流超时
            // 释放ssrc
            if (rtpServerParam.getPresetSsrc() == null) {
                ssrcFactory.releaseSsrc(rtpServerParam.getMediaServerItem().getId(), ssrc);
            }
            // 关闭收流端口
            mediaServerService.closeRTPServer(rtpServerParam.getMediaServerItem(), streamId);
            subscribe.removeSubscribe(rtpHook);
            callback.run(InviteErrorCode.ERROR_FOR_STREAM_TIMEOUT.getCode(), InviteErrorCode.ERROR_FOR_STREAM_TIMEOUT.getMsg(), openRTPServerResult);
        }, userSetting.getPlayTimeout());
        // 开启流到来的监听
        subscribe.addSubscribe(rtpHook, (hookData) -> {
            dynamicTask.stop(timeOutTaskKey);
            // hook响应
            openRTPServerResult.setHookData(hookData);
            callback.run(InviteErrorCode.SUCCESS.getCode(), InviteErrorCode.SUCCESS.getMsg(), openRTPServerResult);
            subscribe.removeSubscribe(rtpHook);
        });

        return ssrcInfo;
    }

    @Override
    public void closeRTPServer(MediaServer mediaServer, SSRCInfo ssrcInfo) {
        if (mediaServer == null) {
            return;
        }
        if (ssrcInfo.getTimeOutTaskKey() != null) {
            dynamicTask.stop(ssrcInfo.getTimeOutTaskKey());
        }
        if (ssrcInfo.getSsrc() != null) {
            // 释放ssrc
            ssrcFactory.releaseSsrc(mediaServer.getId(), ssrcInfo.getSsrc());
        }
        mediaServerService.closeRTPServer(mediaServer, ssrcInfo.getStream());
    }
}
