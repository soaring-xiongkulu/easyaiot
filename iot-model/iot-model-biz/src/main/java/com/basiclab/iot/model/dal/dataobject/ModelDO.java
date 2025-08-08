package com.basiclab.iot.model.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

/**
 * 模型 DO
 *
 * @author IoT
 */
@TableName("model")
@KeySequence("model_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelDO extends BaseEntity {

    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 模型名称
     */
    private String name;
    /**
     * 描述
     */
    private String description;
    /**
     * 封面地址
     */
    private String coverPath;
    /**
     * 模型版本
     */
    private String version;
    /**
     * 发布状态[0:待审核,1:未发布,2:已发布]
     */
    private Short publishStatus;
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
     * git地址
     */
    private String gitUrl;
    /**
     * pt模型地址
     */
    private String ptModelUrl;
    /**
     * pt模型训练结果地址
     */
    private String ptResultUrl;
    /**
     * onnx模型地址
     */
    private String onnxModelUrl;
    /**
     * onnx模型训练结果地址
     */
    private String onnxResultUrl;
    /**
     * rknn模型地址
     */
    private String rknnModelUrl;
    /**
     * rknn模型训练结果地址
     */
    private String rknnResultUrl;

}