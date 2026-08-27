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
     * 包类型[0:软件包,1:固件包,2:APP包,3:PC包]
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
     * 状态[0:未验证,1:测试中,2:已发布,3:待发布,4:已撤回]
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
     * 文件大小（字节）
     */
    @TableField(value = "file_size")
    private Long fileSize;
    /**
     * 原始文件名
     */
    @TableField(value = "file_name")
    private String fileName;
    /**
     * 更新说明
     */
    @TableField(value = "changelog")
    private String changelog;
    /**
     * 发布策略[0:全量,1:灰度]
     */
    @TableField(value = "publish_strategy")
    private Integer publishStrategy;
    /**
     * 灰度阶梯[1:设备级,2:产品级,3:全量]
     */
    @TableField(value = "gray_ladder")
    private Integer grayLadder;
    /**
     * 适用产品标识（空=所有产品）
     */
    @TableField(value = "product_identification")
    private String productIdentification;
    /**
     * 测试是否通过[0:否,1:是]
     */
    @TableField(value = "test_passed")
    private Integer testPassed;
    /**
     * 测试备注
     */
    @TableField(value = "test_remark")
    private String testRemark;
    /**
     * 测试人
     */
    @TableField(value = "test_by")
    private String testBy;
    /**
     * 测试时间
     */
    @TableField(value = "test_time")
    private LocalDateTime testTime;
    /**
     * 撤回原因
     */
    @TableField(value = "withdraw_reason")
    private String withdrawReason;
    /**
     * 撤回时间
     */
    @TableField(value = "withdraw_time")
    private LocalDateTime withdrawTime;

    /**
     * 备注
     */
    @TableField(value = "remark")
    private String remark;
}
