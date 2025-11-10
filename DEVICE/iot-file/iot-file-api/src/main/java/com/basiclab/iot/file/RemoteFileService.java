package com.basiclab.iot.file;

import com.basiclab.iot.common.constant.ServiceNameConstants;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.file.domain.vo.SysFileVo;
import com.basiclab.iot.file.enums.ApiConstants;
import com.basiclab.iot.file.factory.RemoteFileFallbackFactory;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * 文件服务
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(contextId = "remoteFileService", value = ServiceNameConstants.IOT_FILE, fallbackFactory = RemoteFileFallbackFactory.class)
public interface RemoteFileService
{
    /**
     * 上传文件
     *
     * @param file 文件信息
     * @return 结果
     */
    @PostMapping(value = "/sysFile/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public R<SysFileVo> upload(@RequestPart(value = "file") MultipartFile file);

    /**
     * 上传文件（根据桶名称）
     *
     * @param file 文件信息
     * @return 结果
     */
    @PostMapping(value = "/sysFile/uploadByBucket", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public R<SysFileVo> uploadByBucket(@RequestParam(value = "bucketName") String bucketName, @RequestPart(value = "file") MultipartFile file);

    /**
     * 删除文件
     *
     * @param params 请求参数
     * @return 结果
     */
    @PostMapping(value = "/sysFile/removeFile")
    public R<String> removeFile(@RequestBody Map<Object, Object> params);


    /**
     * 获取配置信息
     * @return 结果
     */
    @PostMapping(value = "/sysFile/getDataConfig", consumes = MediaType.APPLICATION_JSON_VALUE)
    public R<Object> getDataConfig();


}
