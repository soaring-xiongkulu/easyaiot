package com.basiclab.iot.stream.transmit;

import com.basiclab.iot.stream.transmit.event.request.ISIPRequestProcessor;
import com.basiclab.iot.stream.transmit.event.response.ISIPResponseProcessor;

import javax.sip.SipListener;

public interface ISIPProcessorObserver extends SipListener {

    void addRequestProcessor(String method, ISIPRequestProcessor processor);

    /**
     * 添加 response订阅
     * @param method 方法名
     * @param processor 处理程序
     */
    void addResponseProcessor(String method, ISIPResponseProcessor processor);

}
