package com.basiclab.iot.node.service.impl;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.Lazy;

import java.lang.reflect.Field;

import static org.junit.jupiter.api.Assertions.assertNotNull;

class NodeSentinelRemediatorServiceImplTest {

    @Test
    void mediaServiceDependencyMustBeLazyToAvoidSentinelMediaBeanCycle() throws Exception {
        Field field = NodeSentinelRemediatorServiceImpl.class.getDeclaredField("nodeMediaService");

        assertNotNull(field.getAnnotation(Lazy.class),
                "NodeMediaService participates in the scheduler/sentinel dependency graph and must be injected lazily");
    }
}
