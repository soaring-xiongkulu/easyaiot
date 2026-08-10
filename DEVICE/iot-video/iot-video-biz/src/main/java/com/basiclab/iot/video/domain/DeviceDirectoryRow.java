package com.basiclab.iot.video.domain;

import lombok.Data;

import java.time.Instant;

@Data
public class DeviceDirectoryRow {

    private Integer id;
    private String name;
    private Integer parentId;
    private String description;
    private int sortOrder;
    private int snapSaveTime = 1;
    private int recordSaveTime = 1;
    private Instant createdAt;
    private Instant updatedAt;
}
