package com.basiclab.iot.sink.codec;

import com.basiclab.iot.sink.mq.message.IotDeviceMessage;

/**
 * {@link IotDeviceMessage} 的编解码器
 *
 * @author 翱翔的雄库鲁
 */
public interface IotDeviceMessageCodec {

    /**
     * 编码消息
     *
     * @param message 消息
     * @return 编码后的消息内容
     */
    byte[] encode(IotDeviceMessage message);

    /**
     * 解码消息
     *
     * @param bytes 消息内容
     * @return 解码后的消息内容
     */
    IotDeviceMessage decode(byte[] bytes);

    /**
     * @return 数据格式（编码器类型）
     * @deprecated 使用 {@link #topic()} 替代
     */
    @Deprecated
    String type();

    /**
     * @return 支持的 Topic 模式（支持通配符，如 /iot/${pid}/${did}/config/push）
     * 如果返回 null，则使用 type() 方法进行匹配（向后兼容）
     */
    String topic();

    /**
     * 判断是否支持该 Topic
     *
     * @param topic 实际的 Topic
     * @return 是否支持
     */
    default boolean supports(String topic) {
        String topicPattern = topic();
        if (topicPattern == null || topicPattern.isEmpty()) {
            return false;
        }
        // 将模板转换为正则表达式
        String regex = topicPattern
                .replace("${pid}", "[^/]+")
                .replace("${did}", "[^/]+")
                .replace("${identifier}", "[^/]+")
                .replace("/", "\\/");
        return topic != null && topic.matches("^" + regex + "$");
    }

}
