package com.basiclab.iot.stream.controller.bean;

import lombok.Data;

import java.util.List;

@Data
public class ChannelToGroupByGbDeviceParam {
    private List<Integer> deviceIds;
    private String parentId;
    private String businessGroup;
}
