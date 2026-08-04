package com.basiclab.iot.infra.dal.dataobject.platformbranding;

import com.basiclab.iot.common.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;

/**
 * 全平台唯一的品牌配置
 */
@TableName("infra_platform_branding")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class PlatformBrandingDO extends BaseDO {

    /**
     * 固定为 1 的全局主键
     */
    @TableId
    private Long id;

    /**
     * 平台名称
     */
    private String platformName;

    /**
     * 平台 Logo 文件编号，空值表示使用内置默认图片
     */
    private Long platformLogoFileId;

    /**
     * 大屏标题
     */
    private String dashboardTitle;

    /**
     * 登录页名称
     */
    private String loginName;

    /**
     * 登录页 Logo 文件编号，空值表示使用内置默认图片
     */
    private Long loginLogoFileId;

    /**
     * 登录表单标题
     */
    private String loginFormTitle;

    /**
     * 浅色登录背景文件编号，空值表示使用内置默认图片
     */
    private Long loginBgLightFileId;

    /**
     * 深色登录背景文件编号，空值表示使用内置默认图片
     */
    private Long loginBgDarkFileId;

    /**
     * 数据库维护的平台名称初始值
     */
    private String defaultPlatformName;

    /**
     * 数据库维护的平台 Logo 初始文件编号
     */
    private Long defaultPlatformLogoFileId;

    /**
     * 数据库维护的大屏标题初始值
     */
    private String defaultDashboardTitle;

    /**
     * 数据库维护的登录页名称初始值
     */
    private String defaultLoginName;

    /**
     * 数据库维护的登录 Logo 初始文件编号
     */
    private Long defaultLoginLogoFileId;

    /**
     * 数据库维护的登录表单标题初始值
     */
    private String defaultLoginFormTitle;

    /**
     * 数据库维护的浅色登录背景初始文件编号
     */
    private Long defaultLoginBgLightFileId;

    /**
     * 数据库维护的深色登录背景初始文件编号
     */
    private Long defaultLoginBgDarkFileId;
}
