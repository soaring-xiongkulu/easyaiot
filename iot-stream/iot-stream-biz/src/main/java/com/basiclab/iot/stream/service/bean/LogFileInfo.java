package com.basiclab.iot.stream.service.bean;

import lombok.Data;

@Data
public class LogFileInfo {

    private String fileName;
    private Long fileSize;
    private Long startTime;
    private Long endTime;

}
