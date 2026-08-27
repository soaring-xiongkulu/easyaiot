package com.basiclab.iot.device.controller.ota;

import com.alibaba.fastjson2.JSONObject;
import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.ota.oo.DmPackageAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageEditOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageExpandGrayOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackagePromoteGrayOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackagePublishOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageTestResultOo;
import com.basiclab.iot.device.domain.ota.oo.DmPackageWithdrawOo;
import com.basiclab.iot.device.domain.ota.qo.DmPackagePageQo;
import com.basiclab.iot.device.domain.ota.qo.DmUpgradeRecordPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmGrayScopeVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackagePageVo;
import com.basiclab.iot.device.domain.ota.vo.DmPackageVersionVo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeRecordVo;
import com.basiclab.iot.device.domain.ota.vo.DmUpgradeStatsVo;
import com.basiclab.iot.device.service.ota.DmPackageService;
import io.swagger.annotations.ApiImplicitParam;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.util.List;

/**
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @desc
 * @created 2025-05-27
 */
@RestController
@RequestMapping("/packages")
@Tag(name  = "版本包")
@Slf4j
public class DmPackageController extends BaseController {

    @Autowired
    private DmPackageService dmPackageService;

    @GetMapping
    @ApiOperation("获取版本包列表")
    public TableDataInfo list(DmPackagePageQo packagePageQo) {
        startPage();
        List<DmPackagePageVo> list = dmPackageService.list(packagePageQo);
        return getDataTable(list);
    }

    @PostMapping("/add")
    @ApiOperation("新增版本包")
    public R<String> createPackage(@RequestBody @Valid DmPackageAddOo dmPackageAddOo) {
        try {
            dmPackageService.createPackage(dmPackageAddOo);
        } catch (Exception e) {
            log.error("Failed to create package,dmPackageAddOo:{} \n",
                    JSONObject.toJSONString(dmPackageAddOo), e);
            return R.fail("版本包创建失败");
        }
        return R.ok("版本包创建成功");
    }

    @TenantIgnore
    @PostMapping("/upload-package")
    @ApiOperation("上传版本包(minio)")
    R<String> uploadPackage(@RequestPart("file") MultipartFile file) {
        try {
            return R.ok(dmPackageService.uploadPackage(file),"上传版本包成功");
        } catch (Exception e) {
            log.error("Failed to upload package,fileName:{} \n",
                    file.getOriginalFilename(), e);
            return R.fail("版本包上传失败");
        }
    }

    @PutMapping
    @ApiOperation("编辑版本包")
    public R<String> editPackage(@RequestBody DmPackageEditOo dmPackageEditOo) {
        try {
            dmPackageService.editPackage(dmPackageEditOo);
        } catch (Exception e) {
            log.error("Failed to edit package,dmPackageEditOo:{} \n"
                    , JSONObject.toJSONString(dmPackageEditOo), e);
            return R.fail("版本包修改失败");
        }
        return R.ok("版本包修改成功");
    }

    @DeleteMapping("/{packageId}")
    @ApiImplicitParam(name = "packageId", value = "版本包ID", required = true, dataType = "Long", dataTypeClass = Long.class)
    @ApiOperation("删除版本包")
    public R deletePackage(@PathVariable("packageId") @Valid Long packageId) {
        try {
            String ret = dmPackageService.deletePackage(packageId);
            return R.ok("版本包删除成功,删除内容:" + ret);
        } catch (Exception e) {
            log.error("Failed to delete package,packageId:{} \n"
                    , packageId, e);
            return R.fail("版本包删除失败");
        }
    }

    @GetMapping("/versions/{type}")
    @ApiImplicitParam(name = "type", value = "包类型[0:软件包,1:固件包,2:APP包,3:PC包]", dataType = "Integer", dataTypeClass = Integer.class)
    @ApiOperation("根据包类型获取版本列表")
    public R<List<DmPackageVersionVo>> versionList(@PathVariable("type") @Valid Integer type) {
        try {
            return R.ok(dmPackageService.versionList(type),"获取版本列表成功");
        } catch (Exception e) {

            log.error("Failed to get product type List,type:{} \n"
                    , type, e);
            return R.fail("获取版本列表失败");
        }
    }

    @PostMapping("/submit-test")
    @ApiImplicitParam(name = "packageId", value = "版本包ID", required = true, dataType = "Long", dataTypeClass = Long.class)
    @ApiOperation("提交测试（未验证 → 测试中）")
    public R submitTest(@RequestParam("packageId") Long packageId) {
        try {
            dmPackageService.submitTest(packageId);
            return R.ok("提交测试成功");
        } catch (Exception e) {
            log.error("Failed to submit test,packageId:{} \n", packageId, e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/test-result")
    @ApiOperation("录入测试结果")
    public R testResult(@RequestBody @Valid DmPackageTestResultOo oo) {
        try {
            dmPackageService.testResult(oo);
            return R.ok("测试结果录入成功");
        } catch (Exception e) {
            log.error("Failed to record test result,oo:{} \n", JSONObject.toJSONString(oo), e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/publish")
    @ApiOperation("发布版本包（全量/灰度）")
    public R publish(@RequestBody @Valid DmPackagePublishOo oo) {
        try {
            dmPackageService.publish(oo);
            return R.ok("发布成功");
        } catch (Exception e) {
            log.error("Failed to publish package,oo:{} \n", JSONObject.toJSONString(oo), e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/expand-gray")
    @ApiOperation("扩大灰度范围")
    public R expandGray(@RequestBody @Valid DmPackageExpandGrayOo oo) {
        try {
            dmPackageService.expandGray(oo);
            return R.ok("扩大灰度范围成功");
        } catch (Exception e) {
            log.error("Failed to expand gray,oo:{} \n", JSONObject.toJSONString(oo), e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/promote-gray")
    @ApiOperation("灰度升阶（设备级→产品级→全量）")
    public R promoteGray(@RequestBody @Valid DmPackagePromoteGrayOo oo) {
        try {
            dmPackageService.promoteGray(oo);
            return R.ok("灰度升阶成功");
        } catch (Exception e) {
            log.error("Failed to promote gray,oo:{} \n", JSONObject.toJSONString(oo), e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/withdraw")
    @ApiOperation("撤回发布")
    public R withdraw(@RequestBody @Valid DmPackageWithdrawOo oo) {
        try {
            dmPackageService.withdraw(oo);
            return R.ok("撤回成功");
        } catch (Exception e) {
            log.error("Failed to withdraw package,oo:{} \n", JSONObject.toJSONString(oo), e);
            return R.fail(e.getMessage());
        }
    }

    @GetMapping("/{pkgId}/gray-scopes")
    @ApiOperation("获取当前灰度范围")
    public R<List<DmGrayScopeVo>> grayScopes(@PathVariable("pkgId") Long pkgId) {
        try {
            return R.ok(dmPackageService.getGrayScopes(pkgId), "获取灰度范围成功");
        } catch (Exception e) {
            log.error("Failed to get gray scopes,pkgId:{} \n", pkgId, e);
            return R.fail("获取灰度范围失败");
        }
    }

    @GetMapping("/{pkgId}/upgrade-stats")
    @ApiOperation("升级统计（漏斗 + 健康度 + 升阶建议）")
    public R<DmUpgradeStatsVo> upgradeStats(@PathVariable("pkgId") Long pkgId) {
        try {
            return R.ok(dmPackageService.getUpgradeStats(pkgId), "获取升级统计成功");
        } catch (Exception e) {
            log.error("Failed to get upgrade stats,pkgId:{} \n", pkgId, e);
            return R.fail("获取升级统计失败");
        }
    }

    @GetMapping("/upgrade-records")
    @ApiOperation("升级记录分页列表")
    public TableDataInfo upgradeRecords(DmUpgradeRecordPageQo qo) {
        startPage();
        List<DmUpgradeRecordVo> list = dmPackageService.getUpgradeRecords(qo);
        return getDataTable(list);
    }

}