package com.basiclab.iot.stream.service;

import com.basiclab.iot.stream.bean.CommonGBChannel;
import com.basiclab.iot.stream.bean.FrontEndControlCodeForPTZ;
import com.basiclab.iot.stream.service.bean.ErrorCallback;

public interface IGbChannelControlService {


    void ptz(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
    void fi(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
    void preset(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
    void tour(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
    void scan(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
    void auxiliary(CommonGBChannel channel, FrontEndControlCodeForPTZ frontEndControlCode, ErrorCallback<String> callback);
}
