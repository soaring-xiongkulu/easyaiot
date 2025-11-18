package com.basiclab.iot.infra.api.file;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.infra.api.file.dto.FileCreateReqDTO;
import com.basiclab.iot.infra.service.file.FileService;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.RestController;
import javax.annotation.Resource;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * FileApiImpl
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController // 提供 RESTful API 接口，给 Feign 调用
@Validated
public class FileApiImpl implements FileApi {

    @Resource
    private FileService fileService;

    @Override
    public CommonResult<String> createFile(FileCreateReqDTO createReqDTO) {
        return success(fileService.createFile(createReqDTO.getName(), createReqDTO.getPath(),
                createReqDTO.getContent()));
    }

}
