package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeFfmpegBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeFfmpegCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeRuntimeCppCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchReqVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleBatchRespVO;
import com.basiclab.iot.node.domain.vo.NodeWorkloadBundleCheckRespVO;
import com.basiclab.iot.node.service.NodeFfmpegDeployService;
import com.basiclab.iot.node.service.NodeRuntimeCppDeployService;
import com.basiclab.iot.node.service.NodeWorkloadBundleService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "管理后台 - 工作负载 bundle 批量分发")
@RestController
@RequestMapping("/node/workload-bundle/")
@Validated
@Slf4j
public class NodeWorkloadBundleController {

    @Resource
    private NodeWorkloadBundleService nodeWorkloadBundleService;
    @Resource
    private NodeFfmpegDeployService nodeFfmpegDeployService;
    @Resource
    private NodeRuntimeCppDeployService nodeRuntimeCppDeployService;

    @PostMapping("/ffmpeg/check-ssh")
    @Operation(summary = "SSH 检测单节点 FFmpeg")
    public CommonResult<NodeFfmpegCheckRespVO> checkFfmpegBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeFfmpegDeployService.checkBySsh(nodeId));
    }

    @PostMapping("/ffmpeg/batch-check-ssh")
    @Operation(summary = "SSH 批量检测 FFmpeg")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchCheckFfmpegBySsh(
            @Valid @RequestBody NodeFfmpegBatchReqVO reqVO) {
        return success(nodeFfmpegDeployService.batchCheckBySsh(reqVO));
    }

    @PostMapping("/ffmpeg/batch-deploy-ssh")
    @Operation(summary = "SSH 批量离线分发 FFmpeg 静态二进制")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchDeployFfmpegBySsh(
            @Valid @RequestBody NodeFfmpegBatchReqVO reqVO) {
        return success(nodeFfmpegDeployService.batchDeployBySsh(reqVO));
    }

    @PostMapping("/ffmpeg/batch-remove-ssh")
    @Operation(summary = "SSH 批量删除 FFmpeg")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchRemoveFfmpegBySsh(
            @Valid @RequestBody NodeFfmpegBatchReqVO reqVO) {
        return success(nodeFfmpegDeployService.batchRemoveBySsh(reqVO));
    }

    @PostMapping("/runtime-cpp/check-ssh")
    @Operation(summary = "SSH 检测单节点 RUNTIME(C++)")
    public CommonResult<NodeRuntimeCppCheckRespVO> checkRuntimeCppBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeRuntimeCppDeployService.checkBySsh(nodeId));
    }

    @PostMapping("/runtime-cpp/batch-check-ssh")
    @Operation(summary = "SSH 批量检测 RUNTIME(C++)")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchCheckRuntimeCppBySsh(
            @Valid @RequestBody NodeRuntimeCppBatchReqVO reqVO) {
        return success(nodeRuntimeCppDeployService.batchCheckBySsh(reqVO));
    }

    @PostMapping("/runtime-cpp/batch-deploy-ssh")
    @Operation(summary = "SSH 批量离线分发 RUNTIME(C++ 高性能执行器)")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchDeployRuntimeCppBySsh(
            @Valid @RequestBody NodeRuntimeCppBatchReqVO reqVO) {
        return success(nodeRuntimeCppDeployService.batchDeployBySsh(reqVO));
    }

    @PostMapping("/runtime-cpp/batch-remove-ssh")
    @Operation(summary = "SSH 批量删除 RUNTIME(C++)")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchRemoveRuntimeCppBySsh(
            @Valid @RequestBody NodeRuntimeCppBatchReqVO reqVO) {
        return success(nodeRuntimeCppDeployService.batchRemoveBySsh(reqVO));
    }

    @PostMapping("/check-ssh")
    @Operation(summary = "SSH 检测单节点 bundle 运行时与脚本")
    public CommonResult<NodeWorkloadBundleCheckRespVO> checkBySsh(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam("bundleType") String bundleType) {
        return success(nodeWorkloadBundleService.checkBySsh(nodeId, bundleType));
    }

    @PostMapping("/batch-check-ssh")
    @Operation(summary = "SSH 批量检测 bundle")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchCheckBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchCheckBySsh(reqVO));
    }

    @PostMapping("/batch-deploy-env-ssh")
    @Operation(summary = "SSH 批量分发离线运行时（pip wheels + site-packages）")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchDeployEnvBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchDeployEnvBySsh(reqVO));
    }

    @PostMapping("/batch-deploy-scripts-ssh")
    @Operation(summary = "SSH 批量分发工作负载脚本")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchDeployScriptsBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchDeployScriptsBySsh(reqVO));
    }

    @PostMapping("/batch-deploy-full-ssh")
    @Operation(summary = "SSH 批量全量分发（VIDEO 含 FFmpeg + RUNTIME + 运行时 + 脚本）")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchDeployFullBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchDeployFullBySsh(reqVO));
    }

    @PostMapping("/batch-remove-env-ssh")
    @Operation(summary = "SSH 批量删除 bundle 运行时")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchRemoveEnvBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchRemoveEnvBySsh(reqVO));
    }

    @PostMapping("/batch-remove-scripts-ssh")
    @Operation(summary = "SSH 批量删除 bundle 脚本（保留共享 app/models）")
    public CommonResult<NodeWorkloadBundleBatchRespVO> batchRemoveScriptsBySsh(
            @Valid @RequestBody NodeWorkloadBundleBatchReqVO reqVO) {
        return success(nodeWorkloadBundleService.batchRemoveScriptsBySsh(reqVO));
    }
}
