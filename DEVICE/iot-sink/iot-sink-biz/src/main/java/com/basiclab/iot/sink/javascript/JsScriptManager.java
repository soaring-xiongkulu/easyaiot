package com.basiclab.iot.sink.javascript;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.script.Compilable;
import javax.script.CompiledScript;
import javax.script.Invocable;
import javax.script.ScriptException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * JsScriptManager
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

@Slf4j
@Component
public class JsScriptManager {

    /**
     * JS 编译缓存，key 为产品标识（productIdentification）
     */
    private final ConcurrentMap<String, CompiledScript> compiledCache = new ConcurrentHashMap<>();

    /**
     * 编译 JS 脚本
     *
     * @param jsText JS 脚本文本
     * @return 编译后的脚本
     * @throws ScriptException 编译失败
     */
    public CompiledScript compileScript(String jsText) throws ScriptException {
        // JS 前加入全局导入
        String js = JsEngine.getJsGlobalImport() + jsText;
        if (log.isDebugEnabled()) {
            log.debug("[compileScript][编译 JS 脚本，长度: {}]", js.length());
        }
        // 编译 JS 脚本
        CompiledScript compiledScript = ((Compilable) JsEngine.getEngine()).compile(js);
        // 初始化，识别和加载脚本中定义的函数
        compiledScript.eval();
        return compiledScript;
    }

    /**
     * 检查脚本是否正确
     *
     * @param jsText JS 脚本文本
     * @return 检查结果，包含成功标志和消息
     */
    public CheckResult checkScript(String jsText) {
        try {
            CompiledScript script = compileScript(jsText);
            Invocable invocable = (Invocable) script.getEngine();

            // 校验 rawDataToProtocol 方法
            try {
                invocable.invokeFunction("rawDataToProtocol", "", new byte[0]);
            } catch (NoSuchMethodException e) {
                log.error("[checkScript][rawDataToProtocol 方法不存在]");
                return new CheckResult(false, "rawDataToProtocol 方法不存在！");
            } catch (Exception e) {
                // 忽略参数错误，只要方法存在即可
            }

            // 校验 protocolToRawData 方法
            try {
                invocable.invokeFunction("protocolToRawData", "", new HashMap<>());
            } catch (NoSuchMethodException e) {
                log.error("[checkScript][protocolToRawData 方法不存在]");
                return new CheckResult(false, "protocolToRawData 方法不存在！");
            } catch (Exception e) {
                // 忽略参数错误，只要方法存在即可
            }

            return new CheckResult(true, "脚本检查通过");
        } catch (ScriptException e) {
            log.error("[checkScript][脚本编译失败]", e);
            return new CheckResult(false, "脚本编译失败：" + e.getMessage());
        }
    }

    /**
     * 脚本检查结果
     */
    public static class CheckResult {
        private final boolean success;
        private final String message;

        public CheckResult(boolean success, String message) {
            this.success = success;
            this.message = message;
        }

        public boolean isSuccess() {
            return success;
        }

        public String getMessage() {
            return message;
        }
    }

    /**
     * 添加产品脚本
     *
     * @param productIdentification 产品标识
     * @param jsText                JS 脚本文本
     * @throws ScriptException 编译失败
     */
    public void addScript(String productIdentification, String jsText) throws ScriptException {
        CompiledScript compiledScript = compileScript(jsText);
        compiledCache.put(productIdentification, compiledScript);
        log.info("[addScript][添加产品脚本成功，产品标识: {}]", productIdentification);
    }

    /**
     * 删除产品脚本
     *
     * @param productIdentification 产品标识
     */
    public void removeScript(String productIdentification) {
        CompiledScript removed = compiledCache.remove(productIdentification);
        if (removed != null) {
            log.info("[removeScript][删除产品脚本成功，产品标识: {}]", productIdentification);
        }
    }

    /**
     * 判断是否有产品脚本
     *
     * @param productIdentification 产品标识
     * @return 是否有脚本
     */
    public boolean hasScript(String productIdentification) {
        return compiledCache.containsKey(productIdentification);
    }

    /**
     * 执行 rawDataToProtocol：将设备原始数据转换为平台标准化格式
     *
     * @param productIdentification 产品标识
     * @param topic                 主题
     * @param rawData               原始数据
     * @return 转换后的数据，如果失败或没有脚本则返回空数组
     */
    public byte[] invokeRawDataToProtocol(String productIdentification, String topic, byte[] rawData) {
        CompiledScript compiledScript = compiledCache.get(productIdentification);
        if (compiledScript == null) {
            log.debug("[invokeRawDataToProtocol][产品脚本不存在，产品标识: {}]", productIdentification);
            return new byte[0];
        }

        try {
            Invocable invocable = (Invocable) compiledScript.getEngine();
            Object result = invocable.invokeFunction("rawDataToProtocol", topic, rawData);
            if (result instanceof byte[]) {
                return (byte[]) result;
            } else {
                log.warn("[invokeRawDataToProtocol][脚本返回类型错误，产品标识: {}]", productIdentification);
                return new byte[0];
            }
        } catch (ScriptException | NoSuchMethodException e) {
            log.error("[invokeRawDataToProtocol][脚本执行失败，产品标识: {}]", productIdentification, e);
            return new byte[0];
        }
    }

    /**
     * 执行 protocolToRawData：将平台标准化格式转换为设备原始数据
     *
     * @param productIdentification 产品标识
     * @param topic                 主题
     * @param jsonData              JSON 数据
     * @return 转换后的原始数据，如果失败或没有脚本则返回空数组
     */
    public byte[] invokeProtocolToRawData(String productIdentification, String topic, Map<String, Object> jsonData) {
        CompiledScript compiledScript = compiledCache.get(productIdentification);
        if (compiledScript == null) {
            log.debug("[invokeProtocolToRawData][产品脚本不存在，产品标识: {}]", productIdentification);
            return new byte[0];
        }

        try {
            Invocable invocable = (Invocable) compiledScript.getEngine();
            Object result = invocable.invokeFunction("protocolToRawData", topic, jsonData);
            if (result instanceof byte[]) {
                return (byte[]) result;
            } else {
                log.warn("[invokeProtocolToRawData][脚本返回类型错误，产品标识: {}]", productIdentification);
                return new byte[0];
            }
        } catch (ScriptException | NoSuchMethodException e) {
            log.error("[invokeProtocolToRawData][脚本执行失败，产品标识: {}]", productIdentification, e);
            return new byte[0];
        }
    }

    /**
     * 获取所有已加载的产品标识
     *
     * @return 产品标识集合
     */
    public java.util.Set<String> getAllLoadedProductIdentifications() {
        return new java.util.HashSet<>(compiledCache.keySet());
    }

    /**
     * 清空所有脚本缓存
     */
    public void clearAll() {
        compiledCache.clear();
        log.info("[clearAll][清空所有脚本缓存]");
    }
}

