package com.basiclab.iot.sink.javascript;

import com.basiclab.iot.common.core.context.TenantContextHolder;
import com.basiclab.iot.sink.dal.dataobject.ProductScriptDO;
import com.basiclab.iot.sink.service.product.ProductScriptService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import javax.annotation.Resource;
import javax.script.ScriptException;
import java.util.List;

/**
 * ProductScriptInitializer
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
@Order(100) // 确保在其他组件初始化之后执行
public class ProductScriptInitializer implements CommandLineRunner {

    @Resource
    private ProductScriptService productScriptService;

    @Resource
    private JsScriptManager jsScriptManager;

    @Override
    public void run(String... args) {
        log.info("[run][开始初始化产品脚本...]");

        try {
            // 1. 从数据库加载所有启用的脚本
            // 忽略租户检查，因为初始化时需要加载所有租户的脚本
            Boolean oldIgnore = TenantContextHolder.isIgnore();
            List<ProductScriptDO> enabledScripts;
            try {
                TenantContextHolder.setIgnore(true);
                enabledScripts = productScriptService.getAllEnabledScripts();
            } finally {
                TenantContextHolder.setIgnore(oldIgnore);
            }
            log.info("[run][从数据库加载到 {} 个启用的产品脚本]", enabledScripts.size());

            // 2. 逐个编译并加载到内存
            int successCount = 0;
            int failCount = 0;

            for (ProductScriptDO script : enabledScripts) {
                String productIdentification = script.getProductIdentification();
                String scriptContent = script.getScriptContent();

                if (scriptContent == null || scriptContent.isEmpty()) {
                    log.warn("[run][产品脚本内容为空，跳过，产品ID: {}, 产品标识: {}]",
                            script.getProductId(), productIdentification);
                    failCount++;
                    continue;
                }

                try {
                    // 编译并加载脚本
                    jsScriptManager.addScript(productIdentification, scriptContent);
                    successCount++;
                    log.debug("[run][加载产品脚本成功，产品ID: {}, 产品标识: {}, 版本: {}]",
                            script.getProductId(), productIdentification, script.getScriptVersion());
                } catch (ScriptException e) {
                    failCount++;
                    log.error("[run][产品脚本编译失败，产品ID: {}, 产品标识: {}]",
                            script.getProductId(), productIdentification, e);
                }
            }

            log.info("[run][产品脚本初始化完成，成功: {}, 失败: {}, 总计: {}]",
                    successCount, failCount, enabledScripts.size());

        } catch (Exception e) {
            log.error("[run][产品脚本初始化失败]", e);
        }
    }
}

