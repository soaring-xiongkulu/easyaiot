package com.basiclab.iot.stream.streamPush.service;

import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.service.bean.ErrorCallback;

public interface IStreamPushPlayService {
    void start(Integer id, ErrorCallback<StreamInfo> callback, String platformDeviceId, String platformName );

    void stop(String app, String stream);

    void stop(Integer id);
}
