package com.basiclab.iot.device.controller.ota;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.device.domain.ota.oo.DmBatchAddVerifyOo;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionAddOo;
import com.basiclab.iot.device.domain.ota.oo.DmDeviceVersionEditOo;
import com.basiclab.iot.device.domain.ota.qo.DmDeviceVersionPageQo;
import com.basiclab.iot.device.domain.ota.qo.DmVerifyPageQo;
import com.basiclab.iot.device.domain.ota.vo.DmDeviceVersionVo;
import com.basiclab.iot.device.domain.ota.vo.DmVerifyVo;
import com.basiclab.iot.device.domain.ota.vo.DmWhiteGroupVo;
import com.basiclab.iot.device.service.ota.DmDeviceVersionService;
import com.basiclab.iot.device.service.ota.DmPackageService;
import io.swagger.annotations.ApiOperation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

/**
 * 设备版本档案 + 测试白名单（/versions 系列）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RestController
@RequestMapping("/versions")
@Tag(name = "设备版本档案")
@Slf4j
public class DmDeviceVersionController extends BaseController {

    @Autowired
    private DmDeviceVersionService dmDeviceVersionService;

    @Autowired
    private DmPackageService dmPackageService;

    @GetMapping
    @ApiOperation("设备版本档案分页列表")
    public TableDataInfo list(DmDeviceVersionPageQo qo) {
        startPage();
        List<DmDeviceVersionVo> list = dmDeviceVersionService.list(qo);
        return getDataTable(list);
    }

    @PostMapping
    @ApiOperation("新增设备版本档案")
    public R<String> create(@RequestBody @Valid DmDeviceVersionAddOo oo) {
        try {
            dmDeviceVersionService.create(oo);
            return R.ok("新增成功");
        } catch (Exception e) {
            log.error("Failed to create device version,oo:{} \n", oo, e);
            return R.fail(e.getMessage());
        }
    }

    @PutMapping
    @ApiOperation("编辑设备版本档案")
    public R<String> edit(@RequestBody @Valid DmDeviceVersionEditOo oo) {
        try {
            dmDeviceVersionService.edit(oo);
            return R.ok("编辑成功");
        } catch (Exception e) {
            log.error("Failed to edit device version,oo:{} \n", oo, e);
            return R.fail(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    @ApiOperation("删除设备版本档案")
    public R<String> delete(@PathVariable("id") Long id) {
        try {
            dmDeviceVersionService.delete(id);
            return R.ok("删除成功");
        } catch (Exception e) {
            log.error("Failed to delete device version,id:{} \n", id, e);
            return R.fail(e.getMessage());
        }
    }

    @GetMapping("/white-list")
    @ApiOperation("测试白名单分页列表")
    public TableDataInfo whiteList(DmVerifyPageQo qo) {
        startPage();
        List<DmVerifyVo> list = dmPackageService.getVerifyList(qo);
        return getDataTable(list);
    }

    @GetMapping("/white-group-list")
    @ApiOperation("白名单分组统计（按产品）")
    public R<List<DmWhiteGroupVo>> whiteGroupList() {
        try {
            return R.ok(dmPackageService.getWhiteGroupList(), "获取分组统计成功");
        } catch (Exception e) {
            log.error("Failed to get white group list \n", e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/batch-add-device-test-list")
    @ApiOperation("批量添加测试白名单设备")
    public R<String> batchAddDeviceTestList(@RequestBody @Valid DmBatchAddVerifyOo oo) {
        try {
            dmPackageService.batchAddVerify(oo);
            return R.ok("添加成功");
        } catch (Exception e) {
            log.error("Failed to batch add verify,oo:{} \n", oo, e);
            return R.fail(e.getMessage());
        }
    }

    @PostMapping("/verification/delete")
    @ApiOperation("删除测试白名单记录")
    public R<String> verificationDelete(@RequestBody List<Long> ids) {
        try {
            dmPackageService.deleteVerify(ids);
            return R.ok("删除成功");
        } catch (Exception e) {
            log.error("Failed to delete verify,ids:{} \n", ids, e);
            return R.fail(e.getMessage());
        }
    }
}
