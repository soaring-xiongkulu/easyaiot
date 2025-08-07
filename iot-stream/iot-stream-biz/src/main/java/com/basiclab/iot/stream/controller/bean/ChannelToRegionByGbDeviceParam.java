package com.basiclab.iot.stream.controller.bean;

import lombok.Data;

import java.util.List;

@Data
public class ChannelToRegionByGbDeviceParam {
    private List<Integer> deviceIds;
    private String civilCode;
}
