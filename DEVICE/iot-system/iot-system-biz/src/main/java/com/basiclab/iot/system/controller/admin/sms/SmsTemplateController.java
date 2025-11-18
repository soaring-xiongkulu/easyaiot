package com.basiclab.iot.system.controller.admin.sms;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.excels.core.util.ExcelUtils;
import com.basiclab.iot.common.utils.object.BeanUtils;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplatePageReqVO;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplateRespVO;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplateSaveReqVO;
import com.basiclab.iot.system.controller.admin.sms.vo.template.SmsTemplateSendReqVO;
import com.basiclab.iot.system.dal.dataobject.sms.SmsTemplateDO;
import com.basiclab.iot.system.service.sms.SmsSendService;
import com.basiclab.iot.system.service.sms.SmsTemplateService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import javax.validation.Valid;
import java.io.IOException;
import java.util.List;

import static com.basiclab.iot.common.domain.CommonResult.success;

/**
 * SmsTemplateController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "管理后台 - 短信模板")
@RestController
@RequestMapping("/system/sms-template")
public class SmsTemplateController {

    @Resource
    private SmsTemplateService smsTemplateService;
    @Resource
    private SmsSendService smsSendService;

    @PostMapping("/create")
    @Operation(summary = "创建短信模板")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:create')")
    public CommonResult<Long> createSmsTemplate(@Valid @RequestBody SmsTemplateSaveReqVO createReqVO) {
        return success(smsTemplateService.createSmsTemplate(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新短信模板")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:update')")
    public CommonResult<Boolean> updateSmsTemplate(@Valid @RequestBody SmsTemplateSaveReqVO updateReqVO) {
        smsTemplateService.updateSmsTemplate(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除短信模板")
    @Parameter(name = "id", description = "编号", required = true)
    //@PreAuthorize("@ss.hasPermission('system:sms-template:delete')")
    public CommonResult<Boolean> deleteSmsTemplate(@RequestParam("id") Long id) {
        smsTemplateService.deleteSmsTemplate(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得短信模板")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:query')")
    public CommonResult<SmsTemplateRespVO> getSmsTemplate(@RequestParam("id") Long id) {
        SmsTemplateDO template = smsTemplateService.getSmsTemplate(id);
        return success(BeanUtils.toBean(template, SmsTemplateRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得短信模板分页")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:query')")
    public CommonResult<PageResult<SmsTemplateRespVO>> getSmsTemplatePage(@Valid SmsTemplatePageReqVO pageVO) {
        PageResult<SmsTemplateDO> pageResult = smsTemplateService.getSmsTemplatePage(pageVO);
        return success(BeanUtils.toBean(pageResult, SmsTemplateRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出短信模板 Excel")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:export')")
    // @ApiAccessLog(operateType = EXPORT)
    public void exportSmsTemplateExcel(@Valid SmsTemplatePageReqVO exportReqVO,
                                       HttpServletResponse response) throws IOException {
        exportReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<SmsTemplateDO> list = smsTemplateService.getSmsTemplatePage(exportReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "短信模板.xls", "数据", SmsTemplateRespVO.class,
                BeanUtils.toBean(list, SmsTemplateRespVO.class));
    }

    @PostMapping("/send-sms")
    @Operation(summary = "发送短信")
    //@PreAuthorize("@ss.hasPermission('system:sms-template:send-sms')")
    public CommonResult<Long> sendSms(@Valid @RequestBody SmsTemplateSendReqVO sendReqVO) {
        return success(smsSendService.sendSingleSmsToAdmin(sendReqVO.getMobile(), null,
                sendReqVO.getTemplateCode(), sendReqVO.getTemplateParams()));
    }

}
