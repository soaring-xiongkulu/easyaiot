package com.basiclab.iot.device.controller.protocol;

import com.basiclab.iot.common.dynamicCompilation.ClassInjector;
import com.basiclab.iot.common.dynamicCompilation.DynamicClassLoader;
import com.basiclab.iot.common.dynamicCompilation.DynamicLoaderEngine;
import com.basiclab.iot.common.dynamicCompilation.bytecode.InjectionSystem;
import com.basiclab.iot.common.domain.AjaxResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.constraints.NotBlank;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.io.PrintWriter;

/**
 * @description: 动态编译代码Controller
 * @packagename: com.basiclab.iot.device.controller.protocol
 * @author: EasyAIoT
 * @email: andywebjava@163.com
 * @date: 2024-07-01 18:31
 **/
@RestController
@RequestMapping("/protocolCompileXcode")
@Slf4j
public class CompileXcodeController {

    /**
     * 动态编译代码
     * @param code
     * @param inparam
     * @return
     */
    @PostMapping("/dynamicallyXcode")
    public AjaxResult importProductJson(@NotBlank(message = "脚本方法块不能为空") String code,@NotBlank(message = "脚本方法块入参不能为空") String inparam) {
        try {
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            PrintWriter out = new PrintWriter(buffer, true);
            byte[] classBytes = DynamicLoaderEngine.compile(code, out, null);
            byte[] injectedClass = ClassInjector.injectSystem(classBytes);
            InjectionSystem.inject(null, new PrintStream(buffer, true), null);
            DynamicClassLoader classLoader = new DynamicClassLoader(this.getClass().getClassLoader());
            DynamicLoaderEngine.executeMain(classLoader, injectedClass, out,inparam);
            return AjaxResult.success(buffer.toString().trim());
        } catch (Throwable e) {
            return AjaxResult.error(e.getMessage());
        }
    }

}
