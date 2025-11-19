package com.basiclab.iot.message.sendlogic;

/**
 * <pre>
 * 消息类型常量
 * </pre>
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-19
 */
public enum MessageTypeEnum {
    /**
     * 消息类型
     */

    ALI_YUN(1, "阿里云短信"),
    TX_YUN(2, "腾讯云短信"),
    EMAIL(3, "E-Mail"),
    WX_CP(4, "微信企业号/企业微信"),
    HTTP(5, "HTTP请求"),
    DING(6, "钉钉");

    private int code;

    private String name;

    public static final int ALI_YUN_CODE = 1;
    public static final int TX_YUN_CODE = 2;
    public static final int EMAIL_CODE = 3;
    public static final int WX_CP_CODE = 4;
    public static final int HTTP_CODE = 5;
    public static final int DING_CODE = 6;

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
            default:
                name = "";
        }
        return name;
    }

}
