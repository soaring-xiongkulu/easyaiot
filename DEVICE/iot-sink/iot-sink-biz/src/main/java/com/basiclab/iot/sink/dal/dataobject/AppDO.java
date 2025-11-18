package com.basiclab.iot.sink.dal.dataobject;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.*;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * AppDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@TableName("app")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AppDO extends BaseEntity2 implements Serializable {

    /**
     * 主键ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 应用ID（AppID）：应用的唯一标识
     */
    private String appId;

    /**
     * 应用密钥（AppKey）：公匙，相当于账号
     */
    private String appKey;

    /**
     * 应用密钥（AppSecret）：私匙，相当于密码
     */
    private String appSecret;

    /**
     * 应用名称
     */
    private String appName;

    /**
     * 应用描述
     */
    private String appDesc;

    /**
     * 状态：ENABLE-启用，DISABLE-禁用
     */
    private String status;

    /**
     * 权限类型：READ_ONLY-只读，READ_WRITE-读写
     */
    private String permissionType;

    /**
     * 过期时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime expireTime;

    /**
     * 租户编号
     */
    private Long tenantId;

    /**
     * 备注
     */
    private String remark;

    /**
     * 是否删除：0-未删除，1-已删除
     */
    @TableLogic
    private Integer deleted;
}

