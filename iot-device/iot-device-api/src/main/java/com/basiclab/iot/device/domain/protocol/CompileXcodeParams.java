package com.basiclab.iot.device.domain.protocol;

import lombok.Data;

import javax.validation.constraints.NotBlank;
import java.io.Serializable;

/**
 * @program: EasyAIoT
 * @description: 动态编译参数
 * @packagename: com.basiclab.iot.device.api.domain.protocol
 * @author EasyAIoT
 * @date: 2025-08-07 23:45
 **/
@Data
public class CompileXcodeParams implements Serializable {
    private static final long serialVersionUID = 1L;

    /**
     * 方法块
     */
    @NotBlank(message = "脚本方法块不能为空")
    private String code;
    /**
     * 方法块入参
     */
    @NotBlank(message = "脚本方法块入参不能为空")
    private String inparam;
}
