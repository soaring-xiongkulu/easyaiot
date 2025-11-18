package com.basiclab.iot.sink.javascript;

import com.basiclab.iot.common.utils.json.JsonUtils;
import com.basiclab.iot.sink.dal.dataobject.ProductScriptDO;
import com.basiclab.iot.sink.messagebus.core.IotMessageBus;
import com.basiclab.iot.sink.messagebus.core.IotMessageSubscriber;
import com.basiclab.iot.sink.service.product.ProductScriptService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.SmartInitializingSingleton;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import javax.script.ScriptException;

/**
 * ProductScriptKafkaSubscriber
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class ProductScriptKafkaSubscriber implements IotMessageSubscriber<String>, SmartInitializingSingleton {

    @Resource
    @Lazy
    private IotMessageBus messageBus;

    @Resource
    private JsScriptManager jsScriptManager;

    @Resource
    private ProductScriptService productScriptService;

    /**
     * Kafka Topic：产品脚本变化通知
     */
    private static final String TOPIC = "iot_product_script_change";

    @Override
    public void afterSingletonsInstantiated() {
        // 在所有单例 bean 初始化完成后注册订阅器，避免循环依赖
        messageBus.register(this);
        log.info("[afterSingletonsInstantiated][产品脚本 Kafka 订阅器初始化完成，订阅主题: {}]", getTopic());
    }

    @Override
    public String getTopic() {
        return TOPIC;
    }

    @Override
    public String getGroup() {
        return "iot-product-script-subscriber";
    }

    @Override
    public void onMessage(String message) {
        try {
            log.debug("[onMessage][接收到产品脚本变化消息: {}]", message);

            // 解析消息，消息格式：{"productId": 123, "productIdentification": "xxx", "action": "update|delete"}
            ProductScriptChangeMessage changeMessage = JsonUtils.parseObject(message, ProductScriptChangeMessage.class);
            if (changeMessage == null) {
                log.warn("[onMessage][消息解析失败，消息: {}]", message);
                return;
            }

            String action = changeMessage.getAction();
            String productIdentification = changeMessage.getProductIdentification();
            Long productId = changeMessage.getProductId();

            if ("delete".equalsIgnoreCase(action)) {
                // 删除脚本
                jsScriptManager.removeScript(productIdentification);
                log.info("[onMessage][删除产品脚本，产品ID: {}, 产品标识: {}]", productId, productIdentification);
            } else if ("update".equalsIgnoreCase(action) || "create".equalsIgnoreCase(action)) {
                // 更新或创建脚本
                updateScript(productId, productIdentification);
            } else {
                log.warn("[onMessage][未知的操作类型: {}]", action);
            }

        } catch (Exception e) {
            log.error("[onMessage][处理产品脚本变化消息失败，消息: {}]", message, e);
        }
    }

    /**
     * 更新脚本
     *
     * @param productId             产品ID
     * @param productIdentification 产品标识
     */
    private void updateScript(Long productId, String productIdentification) {
        try {
            ProductScriptDO script = productScriptService.getScriptByProductIdentification(productIdentification);
            if (script == null) {
                // 脚本不存在或未启用，从内存中移除
                jsScriptManager.removeScript(productIdentification);
                log.info("[updateScript][产品脚本不存在或未启用，移除内存中的脚本，产品ID: {}, 产品标识: {}]",
                        productId, productIdentification);
                return;
            }

            // 脚本存在且启用，加载到内存
            if (script.getScriptContent() == null || script.getScriptContent().isEmpty()) {
                log.warn("[updateScript][产品脚本内容为空，产品ID: {}, 产品标识: {}]", productId, productIdentification);
                jsScriptManager.removeScript(productIdentification);
                return;
            }

            try {
                jsScriptManager.addScript(productIdentification, script.getScriptContent());
                log.info("[updateScript][更新产品脚本成功，产品ID: {}, 产品标识: {}, 版本: {}]",
                        productId, productIdentification, script.getScriptVersion());
            } catch (ScriptException e) {
                log.error("[updateScript][脚本编译失败，产品ID: {}, 产品标识: {}]", productId, productIdentification, e);
                // 编译失败，移除内存中的旧脚本
                jsScriptManager.removeScript(productIdentification);
            }
        } catch (Exception e) {
            log.error("[updateScript][更新产品脚本失败，产品ID: {}, 产品标识: {}]", productId, productIdentification, e);
        }
    }

    /**
     * 产品脚本变化消息
     */
    private static class ProductScriptChangeMessage {
        private Long productId;
        private String productIdentification;
        private String action; // create, update, delete

        public Long getProductId() {
            return productId;
        }

        public void setProductId(Long productId) {
            this.productId = productId;
        }

        public String getProductIdentification() {
            return productIdentification;
        }

        public void setProductIdentification(String productIdentification) {
            this.productIdentification = productIdentification;
        }

        public String getAction() {
            return action;
        }

        public void setAction(String action) {
            this.action = action;
        }
    }
}

