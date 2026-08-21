package com.basiclab.iot.node.service;

import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import com.basiclab.iot.node.dal.dataobject.NodeMetricSnapshotDO;
import org.springframework.web.socket.WebSocketSession;

public interface NodeClusterMetricsBroadcaster {

    void sendSnapshot(WebSocketSession session);

    void broadcastSnapshot();

    void broadcastNodeUpdate(ComputeNodeDO node, NodeMetricSnapshotDO metric);

}
