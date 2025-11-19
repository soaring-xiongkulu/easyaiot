package com.basiclab.iot.message.mino.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文件上传响应体
 * @author zengzhaoyang
 * @date 2025/12/12
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class FileResVo {

    private Integer code;

    private String fileName;

    private String msg;
}
