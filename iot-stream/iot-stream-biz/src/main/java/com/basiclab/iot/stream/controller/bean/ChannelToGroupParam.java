package com.basiclab.iot.stream.controller.bean;

import lombok.Data;

import java.util.List;

@Data
public class ChannelToGroupParam {

    private String parentId;
    private String businessGroup;
    private List<Integer> channelIds;

}
