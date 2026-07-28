package com.basiclab.iot.transform.runtime.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/** 归档对象索引。 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("transform_archive_object")
public class ArchiveObjectDO extends BaseEntity {
    @TableId
    private String id;
    private String eventId;
    private String storagePath;
    private String contentChecksum;
}
