package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.dal.dataobject.ComputeNodeDO;
import lombok.Data;

import java.util.Map;

/**
 * 根据媒体节点 tags 生成设备推流/播放 URL。
 */
public final class MediaUrlBuilder {

    private MediaUrlBuilder() {
    }

    @Data
    public static class StreamUrls {
        private String rtmpStream;
        private String httpStream;
        private String aiRtmpStream;
        private String aiHttpStream;
        private String zlmHost;
        private Integer zlmHttpPort;
        private Integer zlmRtmpPort;
    }

    public static StreamUrls build(ComputeNodeDO srsLiveNode, ComputeNodeDO srsAiNode,
                                   ComputeNodeDO zlmNode, String deviceId, String httpPlayHost) {
        StreamUrls urls = new StreamUrls();
        if (srsLiveNode != null) {
            int rtmpPort = tagInt(srsLiveNode, "srs_rtmp_port", 1935);
            int httpPort = tagInt(srsLiveNode, "srs_http_port", 8080);
            String playHost = StrUtil.blankToDefault(httpPlayHost, srsLiveNode.getHost());
            urls.setRtmpStream(String.format("rtmp://%s:%d/live/%s", srsLiveNode.getHost(), rtmpPort, deviceId));
            urls.setHttpStream(String.format("http://%s:%d/live/%s.flv", playHost, httpPort, deviceId));
        }
        if (srsAiNode != null) {
            int rtmpPort = tagInt(srsAiNode, "srs_rtmp_port", 1935);
            int httpPort = tagInt(srsAiNode, "srs_http_port", 8080);
            String playHost = StrUtil.blankToDefault(httpPlayHost, srsAiNode.getHost());
            urls.setAiRtmpStream(String.format("rtmp://%s:%d/ai/%s", srsAiNode.getHost(), rtmpPort, deviceId));
            urls.setAiHttpStream(String.format("http://%s:%d/ai/%s.flv", playHost, httpPort, deviceId));
        }
        if (zlmNode != null) {
            urls.setZlmHost(zlmNode.getHost());
            urls.setZlmHttpPort(tagInt(zlmNode, "zlm_http_port", 6080));
            urls.setZlmRtmpPort(tagInt(zlmNode, "zlm_rtmp_port", 10935));
        }
        return urls;
    }

    private static int tagInt(ComputeNodeDO node, String key, int defaultValue) {
        Map<String, String> tags = node.getTags();
        if (tags == null || !tags.containsKey(key)) {
            return defaultValue;
        }
        try {
            return Integer.parseInt(tags.get(key).trim());
        } catch (NumberFormatException ignored) {
            return defaultValue;
        }
    }

}
