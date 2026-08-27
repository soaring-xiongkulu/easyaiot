package com.basiclab.iot.device.service.ota.util;

import org.apache.commons.lang3.StringUtils;

/**
 * OTA 版本号比较工具
 * <p>
 * 支持语义化版本（v1.2.3 / 1.2.3.4 / 2025.08.27 等以数字段组成的版本号）：
 * 逐段按数值比较；无法解析为数字段时，回退为字典序比较。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public final class OtaVersionUtils {

    private OtaVersionUtils() {
    }

    /**
     * 比较两个版本号
     *
     * @return a &gt; b 返回正数，a &lt; b 返回负数，相等返回 0
     */
    public static int compare(String a, String b) {
        if (StringUtils.isBlank(a)) {
            return StringUtils.isBlank(b) ? 0 : -1;
        }
        if (StringUtils.isBlank(b)) {
            return 1;
        }
        String left = trimVersion(a);
        String right = trimVersion(b);
        String[] leftParts = left.split("\\.");
        String[] rightParts = right.split("\\.");
        int length = Math.max(leftParts.length, rightParts.length);
        for (int i = 0; i < length; i++) {
            String lp = i < leftParts.length ? leftParts[i] : "0";
            String rp = i < rightParts.length ? rightParts[i] : "0";
            int cmp = comparePart(lp, rp);
            if (cmp != 0) {
                return cmp;
            }
        }
        return 0;
    }

    /**
     * 版本号是否高于目标版本
     */
    public static boolean greaterThan(String version, String target) {
        return compare(version, target) > 0;
    }

    private static String trimVersion(String version) {
        String v = version.trim();
        //去掉 v/V 前缀
        if (v.length() > 1 && (v.charAt(0) == 'v' || v.charAt(0) == 'V')
                && Character.isDigit(v.charAt(1))) {
            v = v.substring(1);
        }
        //去掉前后非数字非点的零散字符（如 release、beta）
        v = v.replaceAll("[^0-9.]", "");
        return v;
    }

    private static int comparePart(String lp, String rp) {
        if (isNumeric(lp) && isNumeric(rp)) {
            return Integer.compare(Integer.parseInt(lp), Integer.parseInt(rp));
        }
        return lp.compareTo(rp);
    }

    private static boolean isNumeric(String s) {
        if (StringUtils.isBlank(s)) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            if (!Character.isDigit(s.charAt(i))) {
                return false;
            }
        }
        return true;
    }
}
