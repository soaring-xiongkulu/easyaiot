package com.basiclab.iot.message.sendlogic;

/**
 * 消息类型枚举
 * 支持6种通知方式：短信(阿里云/腾讯云)、邮件、企业微信、HTTP/webhook、钉钉、飞书
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-19
 */
public enum MessageTypeEnum {
    /** 阿里云短信 */
    ALI_YUN(1, "阿里云短信"),
    /** 腾讯云短信 */
    TX_YUN(2, "腾讯云短信"),
    /** 邮件 */
    EMAIL(3, "E-Mail"),
    /** 企业微信 */
    WX_CP(4, "企业微信"),
    /** HTTP/webhook */
    HTTP(5, "Webhook"),
    /** 钉钉 */
    DING(6, "钉钉"),
    /** 飞书 */
    FEISHU(7, "飞书");

    private int code;

    private String name;

    public static final int ALI_YUN_CODE = 1;
    public static final int TX_YUN_CODE = 2;
    public static final int EMAIL_CODE = 3;
    public static final int WX_CP_CODE = 4;
    public static final int HTTP_CODE = 5;
    public static final int DING_CODE = 6;
    public static final int FEISHU_CODE = 7;

    MessageTypeEnum(int code, String name) {
        this.code = code;
        this.name = name;
    }

    public static String getName(int code) {
        String name = "";
        switch (code) {
            case 1:
                name = ALI_YUN.name;
                break;
            case 2:
                name = TX_YUN.name;
                break;
            case 3:
                name = EMAIL.name;
                break;
            case 4:
                name = WX_CP.name;
                break;
            case 5:
                name = HTTP.name;
                break;
            case 6:
                name = DING.name;
                break;
            case 7:
                name = FEISHU.name;
                break;
            default:
                name = "";
        }
        return name;
    }

}
