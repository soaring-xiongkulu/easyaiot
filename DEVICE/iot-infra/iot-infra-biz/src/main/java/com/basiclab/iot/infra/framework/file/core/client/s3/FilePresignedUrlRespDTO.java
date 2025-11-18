package com.basiclab.iot.infra.framework.file.core.client.s3;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * FilePresignedUrlRespDTO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
public class FilePresignedUrlRespDTO {

    /**
     * 文件上传 URL（用于上传）
     *
     * 例如说：
     */
    private String uploadUrl;

    /**
     * 文件 URL（用于读取、下载等）
     */
    private String url;

}
