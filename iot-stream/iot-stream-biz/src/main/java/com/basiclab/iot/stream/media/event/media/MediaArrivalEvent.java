package com.basiclab.iot.stream.media.event.media;

import com.basiclab.iot.stream.media.bean.MediaInfo;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.media.zlm.dto.hook.OnStreamChangedHookParam;
import com.basiclab.iot.stream.vmanager.bean.StreamContent;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;

/**
 * 流到来事件
 */

public class MediaArrivalEvent extends MediaEvent {
    public MediaArrivalEvent(Object source) {
        super(source);
    }

    public static MediaArrivalEvent getInstance(Object source, OnStreamChangedHookParam hookParam, MediaServer mediaServer, String serverId){
        MediaArrivalEvent mediaArrivalEvent = new MediaArrivalEvent(source);
        mediaArrivalEvent.setMediaInfo(MediaInfo.getInstance(hookParam, mediaServer, serverId));
        mediaArrivalEvent.setApp(hookParam.getApp());
        mediaArrivalEvent.setStream(hookParam.getStream());
        mediaArrivalEvent.setMediaServer(mediaServer);
        mediaArrivalEvent.setSchema(hookParam.getSchema());
        mediaArrivalEvent.setSchema(hookParam.getSchema());
        mediaArrivalEvent.setParamMap(hookParam.getParamMap());
        return mediaArrivalEvent;
    }

    @Getter
    @Setter
    private MediaInfo mediaInfo;

    @Getter
    @Setter
    private String callId;

    @Getter
    @Setter
    private StreamContent streamInfo;

    @Getter
    @Setter
    private Map<String, String> paramMap;

    @Getter
    @Setter
    private String serverId;


}
