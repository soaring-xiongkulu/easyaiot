package com.basiclab.iot.node.service;

import java.util.Map;

public interface NodeCameraAccessService {

    Object execute(Long nodeId, String operation, Map<String, Object> payload);
}
