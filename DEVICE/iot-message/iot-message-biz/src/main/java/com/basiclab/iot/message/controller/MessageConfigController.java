package com.basiclab.iot.message.controller;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.message.domain.entity.MessageConfig;
import com.basiclab.iot.message.domain.model.SendResult;
import com.basiclab.iot.message.sendlogic.msgsender.MailMsgSender;
import com.basiclab.iot.message.service.MessageConfigService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 消息配置controller层
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@RestController
@RequestMapping("/message/config")
@Tag(name  ="消息配置")
public class MessageConfigController {


    @Autowired
    private MessageConfigService messageConfigService;

    @Autowired
    private MailMsgSender mailMsgSender;

    @PostMapping("/add")
    @ApiOperation("新增消息配置")
    public AjaxResult add(@RequestBody MessageConfig messageConfig){
       return messageConfigService.add(messageConfig);
    }

    @PostMapping("/update")
    @ApiOperation("更新消息配置")
    public AjaxResult update(@RequestBody MessageConfig messageConfig){
        return AjaxResult.success(messageConfigService.update(messageConfig));
    }

    @GetMapping("/delete")
    @ApiOperation("删除消息配置")
    public AjaxResult delete(String id){
        return  AjaxResult.success(messageConfigService.delete(id));
    }


    @GetMapping("/query")
    @ApiOperation("查询消息配置")
    public AjaxResult query(@ModelAttribute MessageConfig messageConfig){
        List<MessageConfig> messageConfigs = messageConfigService.query(messageConfig);
        return AjaxResult.success(messageConfigs);
    }

    /**
     * 邮件测试发送
     *
     * @param tos
     * @return
     */
    @GetMapping("/mailSendTest")
    @ApiOperation("邮件发送消息配置")
    public SendResult sendTestMail(String tos){
        return mailMsgSender.sendTestMail(tos);
    }

}
