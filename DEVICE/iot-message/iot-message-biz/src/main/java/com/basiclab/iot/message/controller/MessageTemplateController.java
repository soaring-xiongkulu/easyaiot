package com.basiclab.iot.message.controller;

import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.*;
import com.basiclab.iot.message.mapper.*;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 消息模板控制层controller（查询iot-message服务的消息推送模板）
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@RestController
@RequestMapping("/message/template")
@Tag(name = "消息模板管理")
public class MessageTemplateController extends BaseController {

    @Resource
    private TMsgSmsMapper tMsgSmsMapper;

    @Resource
    private TMsgMailMapper tMsgMailMapper;

    @Resource
    private TMsgWxCpMapper tMsgWxCpMapper;

    @Resource
    private TMsgHttpMapper tMsgHttpMapper;

    @Resource
    private TMsgDingMapper tMsgDingMapper;

    @Resource
    private TMsgFeishuMapper tMsgFeishuMapper;

    /**
     * 根据消息类型查询模板列表
     * 消息类型映射：
     * 1: 短信（阿里云/腾讯云）
     * 3: 邮件
     * 4: 企业微信
     * 5: HTTP
     * 6: 钉钉
     * 7: 飞书
     * 
     * 查询iot-message服务自己的消息推送模板数据
     */
    @GetMapping("/queryByType")
    @ApiOperation("根据消息类型查询模板列表")
    public AjaxResult queryByType(@RequestParam("msgType") Integer msgType) {
        try {
            List<Map<String, Object>> templates = new ArrayList<>();
            
            if (msgType == null) {
                return AjaxResult.error("消息类型不能为空");
            }
            
            // 根据消息类型查询不同的模板
            switch (msgType) {
                case 1:
                    // 短信类型：查询TMsgSms
                    List<TMsgSms> smsList = tMsgSmsMapper.selectByMsgType(msgType);
                    for (TMsgSms sms : smsList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", sms.getId());
                        template.put("name", sms.getMsgName());
                        templates.add(template);
                    }
                    break;
                case 3:
                    // 邮件类型：查询TMsgMail
                    List<TMsgMail> mailList = tMsgMailMapper.selectByMsgType(msgType);
                    for (TMsgMail mail : mailList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", mail.getId());
                        template.put("name", mail.getMsgName());
                        templates.add(template);
                    }
                    break;
                case 4:
                    // 企业微信类型：查询TMsgWxCp
                    List<TMsgWxCp> wxCpList = tMsgWxCpMapper.selectByMsgType(msgType);
                    for (TMsgWxCp wxCp : wxCpList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", wxCp.getId());
                        template.put("name", wxCp.getMsgName());
                        templates.add(template);
                    }
                    break;
                case 5:
                    // HTTP类型：查询TMsgHttp
                    List<TMsgHttp> httpList = tMsgHttpMapper.selectByMsgType(msgType);
                    for (TMsgHttp http : httpList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", http.getId());
                        template.put("name", http.getMsgName());
                        templates.add(template);
                    }
                    break;
                case 6:
                    // 钉钉类型：查询TMsgDing
                    List<TMsgDing> dingList = tMsgDingMapper.selectByMsgType(msgType);
                    for (TMsgDing ding : dingList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", ding.getId());
                        template.put("name", ding.getMsgName());
                        templates.add(template);
                    }
                    break;
                case 7:
                    // 飞书类型：查询TMsgFeishu
                    List<TMsgFeishu> feishuList = tMsgFeishuMapper.selectByMsgType(msgType);
                    for (TMsgFeishu feishu : feishuList) {
                        Map<String, Object> template = new HashMap<>();
                        template.put("id", feishu.getId());
                        template.put("name", feishu.getMsgName());
                        templates.add(template);
                    }
                    break;
                default:
                    return AjaxResult.error("不支持的消息类型: " + msgType);
            }
            
            return AjaxResult.success(templates);
        } catch (Exception e) {
            return AjaxResult.error("查询模板列表失败: " + e.getMessage());
        }
    }
}

