package com.basiclab.iot.stream.controller.bean;

import com.basiclab.iot.stream.common.StreamInfo;
import com.basiclab.iot.stream.bean.Device;
import com.basiclab.iot.stream.vmanager.bean.WVPResult;
import org.springframework.web.context.request.async.DeferredResult;

public class PlayResult {

    private DeferredResult<WVPResult<StreamInfo>> result;
    private String uuid;

    private Device device;

    public DeferredResult<WVPResult<StreamInfo>> getResult() {
        return result;
    }

    public void setResult(DeferredResult<WVPResult<StreamInfo>> result) {
        this.result = result;
    }

    public String getUuid() {
        return uuid;
    }

    public void setUuid(String uuid) {
        this.uuid = uuid;
    }

    public Device getDevice() {
        return device;
    }

    public void setDevice(Device device) {
        this.device = device;
    }
}
