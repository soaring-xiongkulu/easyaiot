package com.basiclab.iot.stream.streamProxy.service;

import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.service.bean.ErrorCallback;
import com.basiclab.iot.stream.streamProxy.bean.StreamProxy;

public interface IStreamProxyPlayService {

    StreamInfo start(int id, Boolean record, ErrorCallback<StreamInfo> callback);

    void start(int id, ErrorCallback<StreamInfo> callback);

    StreamInfo startProxy(StreamProxy streamProxy);

    void stop(int id);

    void stopProxy(StreamProxy streamProxy);
}
