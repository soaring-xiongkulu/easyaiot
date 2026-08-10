package com.basiclab.iot.video.domain;

import lombok.Data;

@Data
public class NvrRow {

    private Integer id;
    private String ip;
    private Integer port;
    private String username;
    private String password;
    private String name;
    private String model;
    private String vendor;
    private String serialNumber;
    private String firmwareVersion;
    private String deviceType;
    private String mac;
    private String scheme;
    private String rtspUrl;
    private String source;
    private String rtspTemplate;
    private Integer rtspPort;
}
