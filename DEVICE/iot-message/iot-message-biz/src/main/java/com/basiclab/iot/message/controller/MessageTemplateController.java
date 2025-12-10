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

    /**
     * 根据ID和消息类型获取模板详情
     * 消息类型映射：
     * 1: 短信（阿里云/腾讯云）
     * 3: 邮件
     * 4: 企业微信
     * 5: HTTP
     * 6: 钉钉
     * 7: 飞书
     * 
     * @param id 模板ID
     * @param msgType 消息类型
     * @return 模板详情，包含userGroupId等字段
     */
    @GetMapping("/get")
    @ApiOperation("根据ID和消息类型获取模板详情")
    public AjaxResult get(@RequestParam("id") String id, @RequestParam("msgType") Integer msgType) {
        try {
            if (id == null || id.trim().isEmpty()) {
                return AjaxResult.error("模板ID不能为空");
            }
            
            if (msgType == null) {
                return AjaxResult.error("消息类型不能为空");
            }
            
            Map<String, Object> template = new HashMap<>();
            
            // 根据消息类型查询不同的模板
            switch (msgType) {
                case 1:
                    // 短信类型：查询TMsgSms
                    TMsgSms sms = tMsgSmsMapper.selectByPrimaryKey(id);
                    if (sms == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", sms.getId());
                    template.put("msgType", sms.getMsgType());
                    template.put("msgName", sms.getMsgName());
                    template.put("templateId", sms.getTemplateId());
                    template.put("content", sms.getContent());
                    template.put("previewUser", sms.getPreviewUser());
                    template.put("userGroupId", sms.getUserGroupId());
                    break;
                case 3:
                    // 邮件类型：查询TMsgMail
                    TMsgMail mail = tMsgMailMapper.selectByPrimaryKey(id);
                    if (mail == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", mail.getId());
                    template.put("msgType", mail.getMsgType());
                    template.put("msgName", mail.getMsgName());
                    template.put("title", mail.getTitle());
                    template.put("cc", mail.getCc());
                    template.put("files", mail.getFiles());
                    template.put("content", mail.getContent());
                    template.put("previewUser", mail.getPreviewUser());
                    template.put("userGroupId", mail.getUserGroupId());
                    break;
                case 4:
                    // 企业微信类型：查询TMsgWxCp
                    TMsgWxCp wxCp = tMsgWxCpMapper.selectByPrimaryKey(id);
                    if (wxCp == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", wxCp.getId());
                    template.put("msgType", wxCp.getMsgType());
                    template.put("msgName", wxCp.getMsgName());
                    template.put("title", wxCp.getTitle());
                    template.put("content", wxCp.getContent());
                    template.put("url", wxCp.getUrl());
                    template.put("btnTxt", wxCp.getBtnTxt());
                    template.put("previewUser", wxCp.getPreviewUser());
                    template.put("userGroupId", wxCp.getUserGroupId());
                    break;
                case 5:
                    // HTTP类型：查询TMsgHttp
                    TMsgHttp http = tMsgHttpMapper.selectByPrimaryKey(id);
                    if (http == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", http.getId());
                    template.put("msgType", http.getMsgType());
                    template.put("msgName", http.getMsgName());
                    template.put("url", http.getUrl());
                    template.put("method", http.getMethod());
                    template.put("headers", http.getHeaders());
                    template.put("body", http.getBody());
                    template.put("previewUser", http.getPreviewUser());
                    template.put("userGroupId", http.getUserGroupId());
                    break;
                case 6:
                    // 钉钉类型：查询TMsgDing
                    TMsgDing ding = tMsgDingMapper.selectByPrimaryKey(id);
                    if (ding == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", ding.getId());
                    template.put("msgType", ding.getMsgType());
                    template.put("msgName", ding.getMsgName());
                    template.put("title", ding.getTitle());
                    template.put("content", ding.getContent());
                    template.put("imgUrl", ding.getImgUrl());
                    template.put("btnTxt", ding.getBtnTxt());
                    template.put("btnUrl", ding.getBtnUrl());
                    template.put("url", ding.getUrl());
                    template.put("previewUser", ding.getPreviewUser());
                    template.put("userGroupId", ding.getUserGroupId());
                    break;
                case 7:
                    // 飞书类型：查询TMsgFeishu
                    TMsgFeishu feishu = tMsgFeishuMapper.selectByPrimaryKey(id);
                    if (feishu == null) {
                        return AjaxResult.error("模板不存在");
                    }
                    template.put("id", feishu.getId());
                    template.put("msgType", feishu.getMsgType());
                    template.put("msgName", feishu.getMsgName());
                    template.put("title", feishu.getTitle());
                    template.put("content", feishu.getContent());
                    template.put("imgUrl", feishu.getImgUrl());
                    template.put("btnTxt", feishu.getBtnTxt());
                    template.put("btnUrl", feishu.getBtnUrl());
                    template.put("url", feishu.getUrl());
                    template.put("previewUser", feishu.getPreviewUser());
                    template.put("userGroupId", feishu.getUserGroupId());
                    break;
                default:
                    return AjaxResult.error("不支持的消息类型: " + msgType);
            }
            
            return AjaxResult.success(template);
        } catch (Exception e) {
            return AjaxResult.error("获取模板详情失败: " + e.getMessage());
        }
    }
}

