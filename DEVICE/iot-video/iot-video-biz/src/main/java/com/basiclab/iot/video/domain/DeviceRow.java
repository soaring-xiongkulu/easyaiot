package com.basiclab.iot.video.domain;

import lombok.Data;

import java.time.Instant;

@Data
public class DeviceRow {

    private String id;
    private String name;
    private String source;
    private String rtmpStream;
    private String httpStream;
    private String aiRtmpStream;
    private String aiHttpStream;
    private Integer stream;
    private String ip;
    private Integer port;
    private String username;
    private String mac;
    private String manufacturer;
    private String model;
    private String firmwareVersion;
    private String serialNumber;
    private String hardwareId;
    private Boolean supportMove;
    private Boolean supportZoom;
    private Integer nvrId;
    private int nvrChannel;
    private String rtspDirect;
    private Boolean channelOnline;
    private String connectionStatus;
    private Boolean enableForward;
    private Integer directoryId;
    private Double longitude;
    private Double latitude;
    private Double altitude;
    private String address;
    private String locationSource;
    private Instant locationUpdatedAt;
    private Double heading;
}
