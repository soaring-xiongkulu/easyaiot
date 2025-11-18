package com.basiclab.iot.device.hooks;

import lombok.Data;
import lombok.ToString;

import java.io.Serializable;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * BaseHook
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@ToString
public abstract class BaseHook implements Serializable {

    /**
     * 事件名称 (每个事件有固定值)
     */
    private String event;

    /**
     * 客户端 ClientId   命名使用deviceIdentification
     */
//    @JSONField(name = "client_id")
    private String clientId;

    /**
     * 客户端 Username，不存在时该值为 "undefined"    命名使用deviceIdentification(过期)
     */
    private String username;


    /**
     * 客户端源 IP 地址 和端口  如:192.168.31.39:51721
     */
    private String peername;

    /**
     * 服务端连接  如：192.168.1.66:1883
     */
    private String sockname;

    /**
     * 协议版本号
     */
    private Integer proto_ver;


    /**
     * 时间戳
     */
    private Long timestamp;


    /**
     * 时间戳(秒)
     */
    private MetaDataMap metadata;

    /**
     * 过期时间
     */
    private Integer expiryInterval;


    public BaseHook(Map<String, Object> map) {
        this.setEvent((String) map.get("event"));
        this.setClientId((String) map.get("clientid"));
        this.setUsername((String) map.get("username"));
        this.setTimestamp((Long) map.get("timestamp"));
        this.setSockname((String) map.get("sockname"));
        this.setPeername((String) map.get("peername"));
        this.setProto_ver((Integer) map.get("proto_ver"));
        this.setExpiryInterval((Integer) map.get("expiry_interval"));
        this.setMetadata(new MetaDataMap((LinkedHashMap) map.get("metadata")));

    }


    @Data
    public class MetaDataMap {

        /**
         * 规则id   设备唯一标识包含在内  {deviceIdentification}_WH_D
         */
        private String ruleId;

        public MetaDataMap(Map<String, Object> map) {
            this.setRuleId((String) map.get("rule_id"));
        }
    }
}
