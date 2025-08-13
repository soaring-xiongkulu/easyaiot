package com.basiclab.iot.model.dal.dataobject;

import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

import java.time.LocalDateTime;
import com.baomidou.mybatisplus.annotation.*;
import com.basiclab.iot.common.core.dataobject.BaseDO;

/**
 * 模型量化服务 DO
 *
 * @author EasyAIoT
 */
@TableName("model_server_quantify")
@KeySequence("model_server_quantify_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelServerQuantifyDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 模型服务ID
     */
    private Long modelServeId;
    /**
     * 模型ID
     */
    private Long modelId;
    /**
     * 模型类型ID
     */
    private Long modelTypeId;
    /**
     * 量化服务版本号
     */
    private String version;
    /**
     * 量化时间
     */
    private LocalDateTime quantifyTime;
    /**
     * 量化状态[0:量化未开始,1:量化中,2:量化成功,3:量化失败]
     */
    private Short quantifyState;
    /**
     * 打包状态[0:打包未开始,1:打包中,2:打包成功,3:打包失败]
     */
    private Short packState;
    /**
     * 量化文件地址
     */
    private String quantifyFileUrl;
    /**
     * 边缘平台
     */
    private String edgePlatform;
    /**
     * 芯片型号
     */
    private String chipModel;
    /**
     * 运行时环境
     */
    private String runEnvironment;
    /**
     * 开发语言
     */
    private String devLanguage;
    /**
     * 部署类型[0:压缩包下载,1:gitee拉取]
     */
    private Short applyType;
    /**
     * 下载或拉取地址
     */
    private String giteeUrl;
    /**
     * 失败原因
     */
    private String reason;
    /**
     * 量化备注
     */
    private String quantifyDescription;
    /**
     * rknn存放目录
     */
    private String rknnDir;

}