package com.basiclab.iot.sink.javascript;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

/**
 * JS 工具函数，提供给 JS 脚本使用
 *
 * @author 翱翔的雄库鲁
 */
public class JsUtilFunction {

    /**
     * 将数据转换为设备请求格式（平台标准化格式）
     *
     * @param data 数据
     * @return 设备请求的字节数组
     */
    public byte[] toDeviceReq(Map<String, Object> data) {
        return toDeviceReq(data, null);
    }

    /**
     * 将数据转换为设备请求格式（平台标准化格式）
     *
     * @param data      数据
     * @param timestamp 时间戳（毫秒），如果为 null 则使用当前时间
     * @return 设备请求的字节数组
     */
    public byte[] toDeviceReq(Map<String, Object> data, Long timestamp) {
        if (timestamp == null) {
            timestamp = System.currentTimeMillis();
        }

        // 构建标准化的设备消息格式
        IotDeviceMessage message = IotDeviceMessage.requestOf(
                "thing.event.property.post", // 属性上报方法
                data
        );
        message.setReportTime(java.time.LocalDateTime.ofInstant(
                java.time.Instant.ofEpochMilli(timestamp),
                java.time.ZoneId.systemDefault()
        ));

        // 转换为 JSON 字节数组
        return JsonUtils.toJsonByte(message);
    }

    /**
     * 将字节数组转换为 JSON 对象
     *
     * @param data 字节数组
     * @return JSON 对象（Map）
     */
    public Map<String, Object> toJsonObject(byte[] data) {
        if (data == null || data.length == 0) {
            return new HashMap<>();
        }
        String json = new String(data, StandardCharsets.UTF_8);
        return JsonUtils.parseObject(json, Map.class);
    }

    /**
     * 将 JSON 字符串转换为对象
     *
     * @param jsonText JSON 字符串
     * @return JSON 对象（Map）
     */
    public Map<String, Object> toJsonObject(String jsonText) {
        if (jsonText == null || jsonText.isEmpty()) {
            return new HashMap<>();
        }
        return JsonUtils.parseObject(jsonText, Map.class);
    }

    /**
     * 转换为整数
     *
     * @param number 数字
     * @return 整数
     */
    public int toInt(Number number) {
        return toInt(number, 0);
    }

    /**
     * 转换为整数
     *
     * @param number       数字
     * @param defaultValue 默认值
     * @return 整数
     */
    public int toInt(Number number, int defaultValue) {
        return number == null ? defaultValue : number.intValue();
    }

    /**
     * 转换为长整数
     *
     * @param number 数字
     * @return 长整数
     */
    public long toLong(Number number) {
        return toLong(number, 0L);
    }

    /**
     * 转换为长整数
     *
     * @param number       数字
     * @param defaultValue 默认值
     * @return 长整数
     */
    public long toLong(Number number, long defaultValue) {
        return number == null ? defaultValue : number.longValue();
    }
}

