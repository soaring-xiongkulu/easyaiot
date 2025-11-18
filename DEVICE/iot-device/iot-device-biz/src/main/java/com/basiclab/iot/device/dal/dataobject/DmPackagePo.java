package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity2;
import lombok.*;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * DmPackagePo
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("device_ota_pkg")
@KeySequence("device_ota_pkg_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DmPackagePo extends BaseEntity2 implements Serializable {

    private static final long serialVersionUID = 3091786858067062715L;
    /**
     * 主键ID
     */
    @TableId
    private Long id;
    /**
     * 包类型[0:软件包,1:固件包,2:电控包]
     */
    @TableField(value = "type")
    private Integer type;
    /**
     * 包名称
     */
    @TableField(value = "name")
    private String name;
    /**
     * 包版本号
     */
    @TableField(value = "version")
    private String version;
    /**
     * 升级方式[0:非强制升级,1:强制升级]
     */
    @TableField(value = "upgrade_mode")
    private Integer upgradeMode;
    /**
     * 包路径
     */
    @TableField(value = "url")
    private String url;
    /**
     * 关键版本标识[0:否,1:是]
     */
    @TableField(value = "key_version_flag")
    private Integer keyVersionFlag;
    /**
     * 状态[0:未验证,1:已验证,2:已发布]
     */
    @TableField(value = "status")
    private Integer status;
    /**
     * 上传时间
     */
    @TableField(value = "upload_time")
    private LocalDateTime uploadTime;
    /**
     * 发布时间
     */
    @TableField(value = "publish_time")
    private LocalDateTime publishTime;
    /**
     * 文件MD5值
     */
    @TableField(value = "file_md5")
    private String fileMd5;

    /**
     * 备注
     */
    @TableField(value = "remark")
    private String remark;
}
