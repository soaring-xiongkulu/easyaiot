package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeSchedulerAllocateRespVO;
import com.basiclab.iot.node.service.NodeSchedulerService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "调度 - 节点分配")
@RestController
@RequestMapping("/node/scheduler/")
@Validated
@Slf4j
public class NodeSchedulerController {

    @Resource
    private NodeSchedulerService nodeSchedulerService;

    @PostMapping("/allocate")
    @Operation(summary = "分配节点")
    public CommonResult<NodeSchedulerAllocateRespVO> allocate(@Valid @RequestBody NodeSchedulerAllocateReqVO reqVO) {
        return success(nodeSchedulerService.allocate(reqVO));
    }

    @PostMapping("/release")
    @Operation(summary = "释放节点绑定")
    public CommonResult<Boolean> release(@RequestParam("workloadType") String workloadType,
                                         @RequestParam("workloadId") String workloadId) {
        nodeSchedulerService.release(workloadType, workloadId);
        return success(true);
    }

}
