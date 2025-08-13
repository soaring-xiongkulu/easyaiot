package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型服务 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server")
@KeySequence("model_server_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 模型服务名称
     */
    private String name;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 数据集ID
     */
    private Long datasetId;
    /**
     * 发布状态[0:待发布,1:已发布,2:发布失败,3:已下架]
     */
    private Short publishStatus;
    /**
     * 审核人ID
     */
    private Long auditUserId;
    /**
     * 版本号
     */
    private String version;
    /**
     * 服务访问地址
     */
    private String serverAddress;
    /**
     * ONNX模型文件
     */
    private String onnxFileUrl;
    /**
     * 描述
     */
    private String description;
    /**
     * 模型大小
     */
    private Long size;
    /**
     * 执行状态[0:未启动,1:部署中,2:部署失败,3:运行中,4:已关闭]
     */
    private Short executeStatus;
    /**
     * 发布时间
     */
    private LocalDateTime publishTime;
    /**
     * anchors.txt文件
     */
    private String anchorsFileUrl;
    /**
     * 完整应用文件（或量化后应用文件）
     */
    private String applyFileUrl;
    /**
     * 应用文件大小
     */
    private Long applyFileSize;
    /**
     * 应用文件MD5值
     */
    private String applyFileMd5;

}