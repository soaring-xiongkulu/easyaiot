package com.basiclab.iot.stream.media.zlm.event;

import com.basiclab.iot.stream.media.bean.MediaServer;
import org.springframework.context.ApplicationEvent;

/**
 * zlm server_start事件
 */
public class HookZlmServerStartEvent extends ApplicationEvent {

    public HookZlmServerStartEvent(Object source) {
        super(source);
    }

    private MediaServer mediaServerItem;

    public MediaServer getMediaServerItem() {
        return mediaServerItem;
    }

    public void setMediaServerItem(MediaServer mediaServerItem) {
        this.mediaServerItem = mediaServerItem;
    }
}
