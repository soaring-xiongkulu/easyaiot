package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.DeviceMediaBindingRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaAllocateReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaDeployReqVO;
import com.basiclab.iot.node.domain.vo.NodeMediaStackCheckRespVO;
import com.basiclab.iot.node.domain.vo.NodeMediaRemoteDeployRespVO;
import com.basiclab.iot.node.domain.vo.NodePortCheckRespVO;
import com.basiclab.iot.node.service.NodeMediaService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "媒体 - 设备流绑定")
@RestController
@RequestMapping("/node/media/")
@Validated
@Slf4j
public class NodeMediaController {

    @Resource
    private NodeMediaService nodeMediaService;

    @PostMapping("/allocate")
    @Operation(summary = "为设备分配 SRS/ZLM 媒体节点并生成流地址")
    public CommonResult<DeviceMediaBindingRespVO> allocate(@Valid @RequestBody NodeMediaAllocateReqVO reqVO) {
        return success(nodeMediaService.allocate(reqVO));
    }

    @GetMapping("/binding")
    @Operation(summary = "查询设备媒体绑定")
    public CommonResult<DeviceMediaBindingRespVO> getBinding(@RequestParam("deviceId") String deviceId) {
        return success(nodeMediaService.getBinding(deviceId));
    }

    @PostMapping("/release")
    @Operation(summary = "释放设备媒体绑定")
    public CommonResult<Boolean> release(@RequestParam("deviceId") String deviceId) {
        nodeMediaService.release(deviceId);
        return success(true);
    }

    @PostMapping("/deploy-stack")
    @Operation(summary = "在媒体节点远程部署 SRS/ZLM 栈")
    public CommonResult<Map<String, Object>> deployStack(@Valid @RequestBody NodeMediaDeployReqVO reqVO) {
        return success(nodeMediaService.deployMediaStack(reqVO));
    }

    @PostMapping("/deploy-ssh")
    @Operation(summary = "通过 SSH 在媒体节点自动部署 SRS/ZLM 栈")
    public CommonResult<NodeMediaRemoteDeployRespVO> deployBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMediaService.deployMediaStackBySsh(nodeId));
    }

    @PostMapping("/check-ssh")
    @Operation(summary = "通过 SSH 检测媒体节点 SRS/ZLM 是否已部署")
    public CommonResult<NodeMediaStackCheckRespVO> checkBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMediaService.checkMediaStackBySsh(nodeId));
    }

    @PostMapping("/check-ports-ssh")
    @Operation(summary = "通过 SSH 检测媒体节点部署端口占用")
    public CommonResult<NodePortCheckRespVO> checkPortsBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMediaService.checkMediaPortsBySsh(nodeId));
    }

    @PostMapping("/stop-ssh")
    @Operation(summary = "通过 SSH 停止目标机 SRS 或 ZLMediaKit 流媒体服务")
    public CommonResult<NodeMediaRemoteDeployRespVO> stopBySsh(
            @RequestParam("nodeId") Long nodeId,
            @RequestParam("service") String service) {
        return success(nodeMediaService.stopMediaServiceBySsh(nodeId, service));
    }

    @PostMapping("/remove-container-ssh")
    @Operation(summary = "通过 SSH 删除目标机 SRS/ZLM 媒体容器")
    public CommonResult<NodeMediaRemoteDeployRespVO> removeContainerBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMediaService.removeMediaContainerBySsh(nodeId));
    }

    @PostMapping("/remove-image-ssh")
    @Operation(summary = "通过 SSH 删除目标机 SRS/ZLM Docker 镜像")
    public CommonResult<NodeMediaRemoteDeployRespVO> removeImageBySsh(@RequestParam("nodeId") Long nodeId) {
        return success(nodeMediaService.removeMediaImageBySsh(nodeId));
    }

}
