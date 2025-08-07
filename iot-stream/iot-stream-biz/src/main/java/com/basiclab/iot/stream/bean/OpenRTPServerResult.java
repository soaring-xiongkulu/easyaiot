package com.basiclab.iot.stream.bean;

import com.basiclab.iot.stream.media.event.hook.HookData;
import com.basiclab.iot.stream.service.bean.SSRCInfo;
import lombok.Data;

@Data
public class OpenRTPServerResult {

    private SSRCInfo ssrcInfo;
    private HookData hookData;
}
