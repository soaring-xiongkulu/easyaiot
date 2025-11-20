package com.basiclab.iot.message.controller;

import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.message.domain.model.vo.MessagePrepareVO;
import com.basiclab.iot.message.service.MessagePrepareService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 消息准备控制层controller
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-18
 */
@RestController
@RequestMapping("/message/prepare")
@Tag(name  ="消息准备管理")
public class MessagePrepareController extends BaseController {

    @Autowired
    private MessagePrepareService messagePrepareService;

    @PostMapping("/add")
    @ApiOperation("新增消息准备信息")
    public AjaxResult add(@RequestBody MessagePrepareVO messagePrepareVO){
        return AjaxResult.success(messagePrepareService.add(messagePrepareVO));
    }

    @PostMapping("/update")
    @ApiOperation("更新消息准备信息")
    public AjaxResult update(@RequestBody MessagePrepareVO messagePrepareVO){
        return AjaxResult.success(messagePrepareService.update(messagePrepareVO));
    }

    @GetMapping("/delete")
    @ApiOperation("删除消息准备信息")
    public AjaxResult delete(int msgType,String id){
        return AjaxResult.success(messagePrepareService.delete(msgType,id));
    }

    @GetMapping("/query")
    @ApiOperation("查询消息准备信息")
    public TableDataInfo query(@ModelAttribute MessagePrepareVO messagePrepareVO){
        startPage();
        List<?> list = messagePrepareService.query(messagePrepareVO);
        return getDataTable(list);
    }


}
