package com.basiclab.iot.rule.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.basiclab.iot.common.web.controller.BaseController;
import com.basiclab.iot.common.domain.AjaxResult;
import com.basiclab.iot.common.domain.TableDataInfo;
import com.basiclab.iot.rule.domain.AlarmRecord;
import com.basiclab.iot.rule.service.AlarmRecordService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * @author IoT
 * @desc
 * @created 2024-07-18
 */
@Tag(name  = "告警信息管理")
@RestController
@RequestMapping("/alarm")
public class AlarmRecordController extends BaseController {

    @Autowired
    private AlarmRecordService alarmRecordService;


    @GetMapping("/list")
    @ApiOperation("规则动作列表")
    public TableDataInfo list(@RequestBody AlarmRecord alarmRecord) {
        startPage();
        LambdaQueryWrapper<AlarmRecord> queryWrapper = Wrappers.lambdaQuery();
        queryWrapper.eq(Objects.nonNull(alarmRecord.getAlarmName()), AlarmRecord::getAlarmName, alarmRecord.getAlarmName());
        queryWrapper.eq(Objects.nonNull(alarmRecord.getAppId()), AlarmRecord::getAppId, alarmRecord.getAppId());
        queryWrapper.eq(Objects.nonNull(alarmRecord.getHandledStatus()), AlarmRecord::getHandledStatus, alarmRecord.getHandledStatus());
        queryWrapper.eq(Objects.nonNull(alarmRecord.getAlarmIdentification()), AlarmRecord::getAlarmIdentification, alarmRecord.getAlarmIdentification());
        queryWrapper.eq(Objects.nonNull(alarmRecord.getHandledTime()), AlarmRecord::getHandledTime, alarmRecord.getHandledTime());
        List<AlarmRecord> list = alarmRecordService.list(queryWrapper);
        return getDataTable(list);
    }

    /**
     * 批量新增
     */
    @PostMapping("/batchInsert")
    @ApiOperation("批量新增")
    public AjaxResult batchInsert(@RequestBody List<AlarmRecord> actionCommandsList) {
        return AjaxResult.success(alarmRecordService.saveBatch(actionCommandsList));
    }

    /**
     * 删除告警信息
     * @param id
     * @return
     */
    @DeleteMapping("remove/{id}")
    @ApiOperation("删除告警信息")
    public AjaxResult remove(@PathVariable Long id) {
        return toAjax(alarmRecordService.removeById(id));
    }

    /**
     * 删除告警信息
     * @param ids
     * @return
     */
    @DeleteMapping("removeList/{ids}")
    @ApiOperation("删除告警信息")
    public AjaxResult remove(@PathVariable Long[] ids) {
        return toAjax(alarmRecordService.removeBatchByIds(Arrays.asList(ids)));
    }

    /**
     * 批量编辑
     */
    @PutMapping("/batchEdit")
    @ApiOperation("批量编辑")
    public AjaxResult updateBatch(@RequestBody List<AlarmRecord> recordList) {
        return toAjax(alarmRecordService.updateBatchById(recordList));
    }

}
