package com.basiclab.iot.sink.javascript;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.script.Bindings;
import javax.script.ScriptContext;
import javax.script.ScriptEngine;
import javax.script.ScriptEngineManager;

/**
 * JsEngine
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */

public enum JsEngine {
    /**
     * 实例
     */
    INSTANCE;

    private static Logger getLog() {
        return LoggerFactory.getLogger(JsEngine.class);
    }

    private final ScriptEngine engine;
    private final String jsGlobalImport;

    JsEngine() {
        ScriptEngineManager manager = new ScriptEngineManager();
        // 尝试获取 JavaScript 引擎
        ScriptEngine jsEngine = manager.getEngineByName("javascript");
        if (jsEngine == null) {
            // 如果 javascript 不可用，尝试 nashorn
            jsEngine = manager.getEngineByName("nashorn");
        }
        if (jsEngine == null) {
            // 如果 nashorn 也不可用，尝试 graal.js
            jsEngine = manager.getEngineByName("graal.js");
        }
        if (jsEngine == null) {
            throw new RuntimeException("无法找到可用的 JavaScript 引擎，请确保已安装 JavaScript 引擎（如 GraalVM）");
        }

        this.engine = jsEngine;
        getLog().info("[JsEngine][初始化 JavaScript 引擎: {}]", jsEngine.getClass().getName());

        // 添加全局工具类
        Bindings globalBindings = engine.createBindings();
        globalBindings.put("jsUtil", new JsUtilFunction());
        engine.setBindings(globalBindings, ScriptContext.GLOBAL_SCOPE);

        // 生成全局导入文本
        this.jsGlobalImport = generateJsGlobalImport();
    }

    /**
     * 生成 JS 全局导入文本
     *
     * @return JS 导入文本
     */
    private String generateJsGlobalImport() {
        StringBuilder builder = new StringBuilder(128);
        // 导入 ReadBuffer
        builder.append("var ReadBuffer = Java.type('")
                .append(ReadBuffer.class.getName())
                .append("');\n");
        // 导入 WriteBuffer
        builder.append("var WriteBuffer = Java.type('")
                .append(WriteBuffer.class.getName())
                .append("');\n");
        return builder.toString();
    }

    /**
     * 获取 engine
     *
     * @return ScriptEngine
     */
    public static ScriptEngine getEngine() {
        return INSTANCE.engine;
    }

    /**
     * 获取 JS 全局导入文本
     *
     * @return JS 导入文本
     */
    public static String getJsGlobalImport() {
        return INSTANCE.jsGlobalImport;
    }
}

