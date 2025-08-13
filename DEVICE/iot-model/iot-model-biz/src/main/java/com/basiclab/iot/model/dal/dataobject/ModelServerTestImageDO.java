package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型测试图片 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server_test_image")
@KeySequence("model_server_test_image_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerTestImageDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 测试模型服务ID
     */
    private Long modelServerTestId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 数据集图片ID
     */
    private Long datasetImageId;
    /**
     * 标注时间
     */
    private LocalDateTime annoTime;
    /**
     * 标注后图片路径
     */
    private String annoImagePath;
    /**
     * 选取次数
     */
    private Integer modificationCount;

}