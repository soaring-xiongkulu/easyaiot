package com.basiclab.iot.transform.runtime.service;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 运行时简易指标。
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Service
public class MetricsService {

    private final AtomicLong accepted = new AtomicLong();
    private final AtomicLong published = new AtomicLong();
    private final AtomicLong delivered = new AtomicLong();
    private final AtomicLong failed = new AtomicLong();
    private final AtomicLong dlq = new AtomicLong();

    public void incAccepted() {
        accepted.incrementAndGet();
    }

    public void incPublished() {
        published.incrementAndGet();
    }

    public void incDelivered() {
        delivered.incrementAndGet();
    }

    public void incFailed() {
        failed.incrementAndGet();
    }

    public void incDlq() {
        dlq.incrementAndGet();
    }

    public Map<String, Long> snapshot() {
        return Map.of(
                "accepted", accepted.get(),
                "published", published.get(),
                "delivered", delivered.get(),
                "failed", failed.get(),
                "dlq", dlq.get()
        );
    }
}
