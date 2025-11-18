package com.basiclab.iot.device.dal.dataobject;

import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.basiclab.iot.common.domain.BaseEntity;
import lombok.*;

/**
 * SnapJobDO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@TableName("video_snap_job")
@KeySequence("video_snap_job_id_seq") // 用于 Oracle、PostgreSQL、Kingbase、DB2、H2 数据库的主键自增。如果是 MySQL 等数据库，可不写。
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SnapJobDO extends BaseEntity {

    /**
     * 主键id
     */
    @TableId
    private Long id;
    /**
     * 任务类型
     */
    private String taskType;
    /**
     * 空间名称
     */
    private String spaceName;
    /**
     * 抓拍任务编号
     */
    private String snapJobIdentification;
    /**
     * 抓拍空间编号
     */
    private String snapSpaceIdentification;
    /**
     * 通道号
     */
    private String channelId;
    /**
     * 设备序列号
     */
    private String deviceId;
    /**
     * 创建人
     */
    private String createBy;
    /**
     * 创建人
     */
    private String updateBy;
    /**
     * 抓拍类型[0:抽帧,1:抓拍]
     */
    private Integer captureType;
    /**
     * cron表达式
     */
    private String cronExpression;
    /**
     * 是否推理[0:否,1:是]
     */
    private Integer algorithmEnabled;
    /**
     * 是否告警[0:否,1:是]
     */
    private Integer alarmEnabled;
    /**
     * 告警类型[0:短信告警,1:邮箱告警]
     */
    private Integer alarmType;
    /**
     * 告警手机号[多个手机号用英文逗号分割]
     */
    private String phoneNumber;
    /**
     * 告警邮箱号[多个邮箱用英文逗号分割]
     */
    private String email;
    /**
     * 算法类型[0:火焰烟雾检测算法,1:人群聚集计数检测算法,2:吸烟检测算法]
     */
    private Integer algorithmType;
    /**
     * 录像解密密钥
     */
    private String videoPassword;
    /**
     * 是否文件自动命名[0:否,1:是]
     */
    private Integer autoFilenameEnabled;
    /**
     * 是否自定义文件前缀[0:否,1:是]
     */
    private Integer customFilenamePrefixEnabled;
    /**
     * 自定义文件前缀
     */
    private String customFilenamePrefix;
    /**
     * 算法阈值表达式
     */
    private String algorithmExpression;
    /**
     * 是否算法仅夜间(23点~8点)启用[0:否,1:是]
     */
    private Integer algorithmNightModeEnabled;
    /**
     * 异常原因
     */
    private String exceptionReason;
    /**
     * 状态[0:正常,1:异常]
     */
    private Integer status;
    /**
     * 是否启用[0:启用,1:停用]
     */
    private Integer isEnabled;

}