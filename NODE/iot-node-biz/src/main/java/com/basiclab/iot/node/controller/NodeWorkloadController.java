package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadDeployRespVO;
import com.basiclab.iot.node.service.NodeCommandService;
import com.basiclab.iot.node.service.NodeSchedulerService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "工作负载 - 远程部署")
@RestController
@RequestMapping("/node/workload/")
@Validated
@Slf4j
public class NodeWorkloadController {

    @Resource
    private NodeCommandService nodeCommandService;
    @Resource
    private NodeSchedulerService nodeSchedulerService;

    @PostMapping("/deploy")
    @Operation(summary = "在指定节点部署工作负载")
    public CommonResult<NodeWorkloadDeployRespVO> deploy(@Valid @RequestBody NodeWorkloadDeployReqVO reqVO) {
        return success(nodeCommandService.deployWorkload(reqVO));
    }

    @PostMapping("/stop")
    @Operation(summary = "停止远程工作负载")
    public CommonResult<Boolean> stop(@RequestParam("nodeId") Long nodeId,
                                      @RequestParam("workloadType") String workloadType,
                                      @RequestParam("workloadId") String workloadId) {
        nodeCommandService.stopWorkload(nodeId, workloadType, workloadId);
        nodeSchedulerService.release(workloadType, workloadId);
        return success(true);
    }

    @PostMapping("/stop-by-id")
    @Operation(summary = "按绑定反查节点后停止工作负载")
    public CommonResult<Boolean> stopById(@RequestParam("workloadType") String workloadType,
                                          @RequestParam("workloadId") String workloadId) {
        nodeCommandService.stopWorkloadByBinding(workloadType, workloadId);
        nodeSchedulerService.release(workloadType, workloadId);
        return success(true);
    }

}
