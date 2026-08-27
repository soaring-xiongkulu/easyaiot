package com.basiclab.iot.device.controller.ota;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.device.domain.ota.oo.DmOtaCheckOo;
import com.basiclab.iot.device.domain.ota.oo.DmOtaReportOo;
import com.basiclab.iot.device.domain.ota.vo.OtaUpgradeItemVo;
import com.basiclab.iot.device.service.ota.DmOtaService;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.util.List;

/**
 * 设备侧统一 OTA 出入口（管理端直连）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("/ota")
@Tag(name = "OTA统一出入口")
@Slf4j
public class DmOtaController {

    @Autowired
    private DmOtaService dmOtaService;

    @PostMapping("/check")
    @ApiOperation("设备升级检测（一次携带全部类型当前版本）")
    public R<List<OtaUpgradeItemVo>> check(@RequestBody @Valid DmOtaCheckOo oo) {
        try {
            return R.ok(dmOtaService.check(oo), "检测完成");
        } catch (Exception e) {
            log.error("Failed to check ota,oo:{} \n", oo, e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/report")
    @ApiOperation("设备升级进度/结果上报")
    public R<Boolean> report(@RequestBody @Valid DmOtaReportOo oo) {
        try {
            dmOtaService.report(oo);
            return R.ok(true, "上报成功");
        } catch (Exception e) {
            log.error("Failed to report ota,oo:{} \n", oo, e);
            return R.fail(e.getMessage());
        }
    }
}
