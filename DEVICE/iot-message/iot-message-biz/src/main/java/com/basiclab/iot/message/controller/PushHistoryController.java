package com.basiclab.iot.message.controller;

import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.message.domain.entity.TPushHistory;
import com.basiclab.iot.message.service.PushHistoryService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 推送历史controller
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@RestController
@RequestMapping("/message/push/history")
@Tag(name  ="推送历史")
public class PushHistoryController extends BaseController {
    @Autowired
    private PushHistoryService pushHistoryService;

    @GetMapping("/query")
    @ApiOperation("查询推送历史")
    public TableDataInfo query(@ModelAttribute TPushHistory tPushHistory){
        List<TPushHistory> list = pushHistoryService.query(tPushHistory);
        return getDataTable(list);
    }
}
