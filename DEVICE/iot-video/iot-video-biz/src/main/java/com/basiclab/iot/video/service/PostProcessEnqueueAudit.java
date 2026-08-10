package com.basiclab.iot.video.service;

import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/**
 * In-process enqueue telemetry for certify side_effect sampling (mini stub path).
 */
public final class PostProcessEnqueueAudit {

    private static final AtomicInteger ENQUEUE_COUNT = new AtomicInteger(0);
    private static final AtomicReference<String> LAST_ENQUEUE_URL = new AtomicReference<>(null);
    private static final AtomicReference<Boolean> LAST_ENQUEUE_OK = new AtomicReference<>(null);

    private PostProcessEnqueueAudit() {
    }

    public static void record(String enqueueUrl, boolean ok) {
        ENQUEUE_COUNT.incrementAndGet();
        LAST_ENQUEUE_URL.set(enqueueUrl);
        LAST_ENQUEUE_OK.set(ok);
    }

    public static int enqueueCount() {
        return ENQUEUE_COUNT.get();
    }

    public static String lastEnqueueUrl() {
        return LAST_ENQUEUE_URL.get();
    }

    public static Boolean lastEnqueueOk() {
        return LAST_ENQUEUE_OK.get();
    }

    public static void reset() {
        ENQUEUE_COUNT.set(0);
        LAST_ENQUEUE_URL.set(null);
        LAST_ENQUEUE_OK.set(null);
    }
}
