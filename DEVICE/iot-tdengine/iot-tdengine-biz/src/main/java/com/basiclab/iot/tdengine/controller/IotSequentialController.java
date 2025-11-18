package com.basiclab.iot.tdengine.controller;

import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.tdengine.domain.IotSequential;
import com.basiclab.iot.tdengine.service.IotSequentialService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * IotSequentialController
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RequestMapping("/sequential")
@RestController
public class IotSequentialController extends BaseController {

    @Autowired
    private IotSequentialService iotSequentialService;

    @GetMapping("/getList")
    public TableDataInfo getList(@RequestBody IotSequential iotSequential) {
        startPage();
        List<IotSequential> list = iotSequentialService.getList(iotSequential);
        return getDataTable(list);
    }

    /**
     * 根据时序时间查询详情
     *
     * @param startTime
     * @return
     */
    @GetMapping("/selectByTime")
    public AjaxResult selectByTime(@PathVariable String startTime) {
        IotSequential iotSequential = iotSequentialService.selectByTime(startTime);
        return AjaxResult.success(iotSequential);
    }

    /**
     * 添加
     *
     * @param iotSequential
     * @return
     */
    @PostMapping("/save")
    public int save(@RequestBody IotSequential iotSequential) {
        return iotSequentialService.save(iotSequential);
    }
}
