package com.basiclab.iot.stream.vmanager.bean;

import com.basiclab.iot.stream.common.VersionPo;
import com.basiclab.iot.stream.config.SipConfig;
import com.basiclab.iot.stream.config.UserSetting;
import lombok.Data;

@Data
public class SystemConfigInfo {

    private int serverPort;
    private SipConfig sip;
    private UserSetting addOn;
    private VersionPo version;

}

