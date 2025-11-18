package com.basiclab.iot.system.api.social;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.system.api.social.dto.SocialWxJsapiSignatureRespDTO;
import com.basiclab.iot.system.api.social.dto.SocialWxPhoneNumberInfoRespDTO;
import com.basiclab.iot.system.enums.ApiConstants;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Parameters;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * SocialClientApi
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@FeignClient(name = ApiConstants.NAME) // TODO BasicLab：fallbackFactory =
@Tag(name = "RPC 服务 - 社交应用")
public interface SocialClientApi {

    String PREFIX = ApiConstants.PREFIX + "/social-client";

    @GetMapping(PREFIX + "/get-authorize-url")
    @Operation(summary = "获得社交平台的授权 URL")
    @Parameters({
            @Parameter(name = "socialType", description = "社交平台的类型", example = "1", required = true),
            @Parameter(name = "userType", description = "用户类型", example = "1", required = true),
            @Parameter(name = "redirectUri", description = "重定向 URL", example = "https://www.iocoder.cn", required = true)
    })
    CommonResult<String> getAuthorizeUrl(@RequestParam("socialType") Integer socialType,
                                         @RequestParam("userType") Integer userType,
                                         @RequestParam("redirectUri") String redirectUri);

    @GetMapping(PREFIX + "/create-wx-mp-jsapi-signature")
    @Operation(summary = "创建微信公众号 JS SDK 初始化所需的签名")
    @Parameters({
            @Parameter(name = "userType", description = "用户类型", example = "1", required = true),
            @Parameter(name = "url", description = "访问 URL", example = "https://www.iocoder.cn", required = true)
    })
    CommonResult<SocialWxJsapiSignatureRespDTO> createWxMpJsapiSignature(@RequestParam("userType") Integer userType,
                                                                         @RequestParam("url") String url);

    @GetMapping(PREFIX + "/create-wx-ma-phone-number-info")
    @Operation(summary = "获得微信小程序的手机信息")
    @Parameters({
            @Parameter(name = "userType", description = "用户类型", example = "1", required = true),
            @Parameter(name = "phoneCode", description = "手机授权码", example = "Yudao11", required = true)
    })
    CommonResult<SocialWxPhoneNumberInfoRespDTO> getWxMaPhoneNumberInfo(@RequestParam("userType") Integer userType,
                                                                        @RequestParam("phoneCode") String phoneCode);

}
