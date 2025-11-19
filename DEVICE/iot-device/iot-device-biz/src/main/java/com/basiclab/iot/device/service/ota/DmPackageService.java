package com.basiclab.iot.device.service.ota;


import com.basiclab.iot.device.domain.ota.oo.DmPackageAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageEditOo;
import com.basiclab.iot.device.domain.ota.qo.DmPackagePageQo;
import com.basiclab.iot.device.domain.ota.vo.DmPackagePageVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackageVersionVo;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-28
 */
public interface DmPackageService {

    List<DmPackagePageVo> list(DmPackagePageQo packagePageQo);

    void createPackage(DmPackageAddOo dmPackageAddOo) throws IOException;

    String uploadPackage(MultipartFile file) throws Exception;

    void editPackage(DmPackageEditOo dmPackageEditOo) throws IOException;

    String deletePackage(Long packageId);

    List<DmPackageVersionVo> versionList(Integer type);
}
