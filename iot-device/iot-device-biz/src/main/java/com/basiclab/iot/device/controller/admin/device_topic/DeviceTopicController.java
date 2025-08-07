package com.basiclab.iot.device.controller.admin.device_topic;

import com.basiclab.iot.device.dal.dataobject.device_topic.DeviceTopicDO;
import org.springframework.web.bind.annotation.*;
import javax.annotation.Resource;
import org.springframework.validation.annotation.Validated;
import org.springframework.security.access.prepost.PreAuthorize;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.Operation;

import javax.validation.*;
import javax.servlet.http.*;
import java.util.*;
import java.io.IOException;

import com.basiclab.iot.common.domain.PageParam;
import com.basiclab.iot.common.domain.PageResult;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.common.utils.object.BeanUtils;
import static com.basiclab.iot.common.domain.CommonResult.success;

import com.basiclab.iot.common.excel.core.util.ExcelUtils;

import com.basiclab.iot.common.apilog.core.annotation.ApiAccessLog;
import static com.basiclab.iot.common.apilog.core.enums.OperateTypeEnum.*;

import com.basiclab.iot.device.controller.admin.device_topic.vo.*;
import com.basiclab.iot.device.service.device_topic.TopicService;

@Tag(name = "管理后台 - 设备Topic数据")
@RestController
@RequestMapping("/device/topic")
@Validated
public class DeviceTopicController {

    @Resource
    private TopicService topicService;

    @PostMapping("/create")
    @Operation(summary = "创建设备Topic数据")
    @PreAuthorize("@ss.hasPermission('device:topic:create')")
    public CommonResult<Long> createTopic(@Valid @RequestBody DeviceTopicSaveReqVO createReqVO) {
        return success(topicService.createTopic(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新设备Topic数据")
    @PreAuthorize("@ss.hasPermission('device:topic:update')")
    public CommonResult<Boolean> updateTopic(@Valid @RequestBody DeviceTopicSaveReqVO updateReqVO) {
        topicService.updateTopic(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除设备Topic数据")
    @Parameter(name = "id", description = "编号", required = true)
    @PreAuthorize("@ss.hasPermission('device:topic:delete')")
    public CommonResult<Boolean> deleteTopic(@RequestParam("id") Long id) {
        topicService.deleteTopic(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得设备Topic数据")
    @Parameter(name = "id", description = "编号", required = true, example = "1024")
    @PreAuthorize("@ss.hasPermission('device:topic:query')")
    public CommonResult<DeviceTopicRespVO> getTopic(@RequestParam("id") Long id) {
        DeviceTopicDO topic = topicService.getTopic(id);
        return success(BeanUtils.toBean(topic, DeviceTopicRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得设备Topic数据分页")
    @PreAuthorize("@ss.hasPermission('device:topic:query')")
    public CommonResult<PageResult<DeviceTopicRespVO>> getTopicPage(@Valid DeviceTopicPageReqVO pageReqVO) {
        PageResult<DeviceTopicDO> pageResult = topicService.getTopicPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, DeviceTopicRespVO.class));
    }

    @GetMapping("/export-excel")
    @Operation(summary = "导出设备Topic数据 Excel")
    @PreAuthorize("@ss.hasPermission('device:topic:export')")
    @ApiAccessLog(operateType = EXPORT)
    public void exportTopicExcel(@Valid DeviceTopicPageReqVO pageReqVO,
              HttpServletResponse response) throws IOException {
        pageReqVO.setPageSize(PageParam.PAGE_SIZE_NONE);
        List<DeviceTopicDO> list = topicService.getTopicPage(pageReqVO).getList();
        // 导出 Excel
        ExcelUtils.write(response, "设备Topic数据.xls", "数据", DeviceTopicRespVO.class,
                        BeanUtils.toBean(list, DeviceTopicRespVO.class));
    }

}