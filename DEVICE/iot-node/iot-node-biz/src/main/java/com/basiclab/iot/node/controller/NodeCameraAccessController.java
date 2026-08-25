package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeCameraAccessReqVO;
import com.basiclab.iot.node.service.NodeCameraAccessService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.validation.Valid;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "节点管理 - 摄像头接入代理")
@RestController
@RequestMapping("/node/camera-access")
@Validated
public class NodeCameraAccessController {

    @Resource
    private NodeCameraAccessService nodeCameraAccessService;

    @PostMapping("/{operation}")
    @Operation(summary = "在指定节点执行摄像头发现、扫描或源流探测")
    public CommonResult<Object> execute(
            @PathVariable("operation") String operation,
            @Valid @RequestBody NodeCameraAccessReqVO reqVO) {
        return success(nodeCameraAccessService.execute(
                reqVO.getNodeId(), operation, reqVO.getPayload()));
    }
}
