package com.basiclab.iot.stream.service;

import com.basiclab.iot.stream.bean.OpenRTPServerResult;
import com.basiclab.iot.stream.media.bean.MediaServer;
import com.basiclab.iot.stream.media.event.media.MediaArrivalEvent;
import com.basiclab.iot.stream.media.event.media.MediaDepartureEvent;
import com.basiclab.iot.stream.service.bean.ErrorCallback;
import com.basiclab.iot.stream.service.bean.RTPServerParam;
import com.basiclab.iot.stream.service.bean.SSRCInfo;
import org.springframework.context.event.EventListener;
import org.springframework.scheduling.annotation.Async;

public interface IReceiveRtpServerService {
    SSRCInfo openRTPServer(RTPServerParam rtpServerParam, ErrorCallback<OpenRTPServerResult> callback);

    void closeRTPServer(MediaServer mediaServer, SSRCInfo ssrcInfo);

    /**
     * 流到来的处理
     */
    @Async("taskExecutor")
    @EventListener
    void onApplicationEvent(MediaArrivalEvent event);

    /**
     * 流离开的处理
     */
    @Async("taskExecutor")
    @EventListener
    void onApplicationEvent(MediaDepartureEvent event);
}
