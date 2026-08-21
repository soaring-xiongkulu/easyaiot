package com.basiclab.iot.node.controller;

import com.basiclab.iot.common.core.aop.TenantIgnore;
import com.basiclab.iot.common.domain.CommonResult;
import com.basiclab.iot.node.domain.vo.NodeAgentHeartbeatReqVO;
import com.basiclab.iot.node.domain.vo.NodeAgentRegisterReqVO;
import com.basiclab.iot.node.service.NodeAgentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.validation.Valid;
import java.util.Collections;
import java.util.Map;

import static com.basiclab.iot.common.domain.CommonResult.success;

@Tag(name = "Agent - 节点代理")
@RestController
@RequestMapping("/node/agent/")
@Validated
@Slf4j
public class NodeAgentController {

    @Resource
    private NodeAgentService nodeAgentService;

    @PostMapping("/register")
    @Operation(summary = "Agent 注册")
    @TenantIgnore
    public CommonResult<Map<String, Object>> register(@Valid @RequestBody NodeAgentRegisterReqVO reqVO) {
        nodeAgentService.register(reqVO);
        return success(Collections.singletonMap("ttl_sec", 30));
    }

    @PostMapping("/heartbeat")
    @Operation(summary = "Agent 心跳")
    @TenantIgnore
    public CommonResult<Boolean> heartbeat(
            @Valid @RequestBody NodeAgentHeartbeatReqVO reqVO,
            javax.servlet.http.HttpServletRequest request) {
        if (log.isDebugEnabled()) {
            log.debug("Agent heartbeat nodeId={}, memTotal={}, diskTotal={}, remote={}",
                    reqVO.getNodeId(), reqVO.getMemTotalBytes(), reqVO.getDiskTotalBytes(),
                    request.getRemoteAddr());
        }
        nodeAgentService.heartbeat(reqVO);
        return success(true);
    }

}
