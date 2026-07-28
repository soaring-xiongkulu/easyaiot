package com.basiclab.iot.transform.runtime.dal;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import org.apache.ibatis.reflection.MetaObject;
import org.springframework.stereotype.Component;

import java.time.Instant;

/** Supplies auditable timestamps without coupling TRANSFORM to iot-common. */
@Component
public class PersistenceMetaObjectHandler implements MetaObjectHandler {
    @Override public void insertFill(MetaObject metaObject) {
        strictInsertFill(metaObject, "createTime", Instant.class, Instant.now());
        strictInsertFill(metaObject, "updateTime", Instant.class, Instant.now());
        strictInsertFill(metaObject, "deleted", Integer.class, 0);
    }
    @Override public void updateFill(MetaObject metaObject) {
        strictUpdateFill(metaObject, "updateTime", Instant.class, Instant.now());
    }
}
