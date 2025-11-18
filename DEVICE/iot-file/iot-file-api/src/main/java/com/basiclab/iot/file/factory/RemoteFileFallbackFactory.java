package com.basiclab.iot.file.factory;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.file.RemoteFileService;
import com.basiclab.iot.file.domain.vo.SysFileVo;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * 文件服务降级处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Component
public class RemoteFileFallbackFactory implements FallbackFactory<RemoteFileService> {
    private static final Logger log = LoggerFactory.getLogger(RemoteFileFallbackFactory.class);

    @Override
    public RemoteFileService create(Throwable throwable) {
        log.error("文件服务调用失败:{}", throwable.getMessage());
        return new RemoteFileService() {
            @Override
            public R<SysFileVo> upload(MultipartFile file) {
                return R.fail("上传文件失败:" + throwable.getMessage());
            }

            @Override
            public R<SysFileVo> uploadByBucket(String bucketName, MultipartFile file) {
                return R.fail("上传文件（根据桶名称）失败:" + throwable.getMessage());
            }

            @Override
            public R<String> removeFile(@RequestBody Map<Object, Object> params) {
                return R.fail("删除文件失败: " + throwable.getMessage());
            }

            @Override
            public R<Object> getDataConfig() {
                return R.fail("获取配置信息失败: " + throwable.getMessage());
            }

        };
    }
}
