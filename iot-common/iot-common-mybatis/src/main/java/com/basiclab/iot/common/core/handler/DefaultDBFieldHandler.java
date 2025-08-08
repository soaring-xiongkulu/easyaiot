package com.basiclab.iot.common.core.handler;

import com.baomidou.mybatisplus.core.handlers.MetaObjectHandler;
import com.basiclab.iot.common.core.dataobject.BaseDO;
import com.basiclab.iot.common.domain.BaseEntity;
import com.basiclab.iot.common.domain.BaseEntity2;
import com.basiclab.iot.common.web.core.util.WebFrameworkUtils;
import org.apache.ibatis.reflection.MetaObject;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * 通用参数填充实现类
 *
 * 如果没有显式的对通用参数进行赋值，这里会对通用参数进行填充、赋值
 *
 * @author hexiaowu
 */
public class DefaultDBFieldHandler implements MetaObjectHandler {

    @Override
    public void insertFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseDO) {
            BaseDO baseDO = (BaseDO) metaObject.getOriginalObject();

            LocalDateTime current = LocalDateTime.now();
            // 创建时间为空，则以当前时间为插入时间
            baseDO.setCreateTime(current);
            // 更新时间为空，则以当前时间为更新时间
            baseDO.setUpdateTime(current);

            Long userId = WebFrameworkUtils.getLoginUserId();
            // 当前登录用户不为空，创建人为空，则当前登录用户为创建人
            if (Objects.nonNull(userId) && Objects.isNull(baseDO.getCreator())) {
                baseDO.setCreator(userId.toString());
            }
            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            if (Objects.nonNull(userId) && Objects.isNull(baseDO.getUpdater())) {
                baseDO.setUpdater(userId.toString());
            }
        } else if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseEntity) {//兼容旧代码
            BaseEntity baseEntity = (BaseEntity) metaObject.getOriginalObject();

            LocalDateTime current = LocalDateTime.now();
            // 创建时间为空，则以当前时间为插入时间
            baseEntity.setCreateTime(current);
            // 更新时间为空，则以当前时间为更新时间
            baseEntity.setUpdateTime(current);

            Long userId = WebFrameworkUtils.getLoginUserId();
            // 当前登录用户不为空，创建人为空，则当前登录用户为创建人
            if (Objects.nonNull(userId) && Objects.isNull(baseEntity.getCreateBy())) {
                baseEntity.setCreateBy("admin");
            }
            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            if (Objects.nonNull(userId) && Objects.isNull(baseEntity.getUpdateBy())) {
                baseEntity.setUpdateBy("admin");
            }
        } else if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseEntity2) {//兼容旧代码
            BaseEntity2 baseEntity = (BaseEntity2) metaObject.getOriginalObject();

            LocalDateTime current = LocalDateTime.now();
            // 创建时间为空，则以当前时间为插入时间
            baseEntity.setCreatedTime(current);
            // 更新时间为空，则以当前时间为更新时间
            baseEntity.setUpdatedTime(current);

            Long userId = WebFrameworkUtils.getLoginUserId();
            // 当前登录用户不为空，创建人为空，则当前登录用户为创建人
            if (Objects.nonNull(userId) && Objects.isNull(baseEntity.getCreatedBy())) {
                baseEntity.setCreatedBy("admin");
            }
            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            if (Objects.nonNull(userId) && Objects.isNull(baseEntity.getUpdatedBy())) {
                baseEntity.setUpdatedBy("admin");
            }
        }
    }

    @Override
    public void updateFill(MetaObject metaObject) {
        if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseDO) {
            // 更新时间为空，则以当前时间为更新时间
            setFieldValByName("updateTime", LocalDateTime.now(), metaObject);

            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            Object modifier = getFieldValByName("updater", metaObject);
            Long userId = WebFrameworkUtils.getLoginUserId();
            if (Objects.nonNull(userId) && Objects.isNull(modifier)) {
                setFieldValByName("updater", userId.toString(), metaObject);
            }
        } else if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseEntity) {//兼容旧代码
            // 更新时间为空，则以当前时间为更新时间
            setFieldValByName("updateTime", LocalDateTime.now(), metaObject);

            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            Object modifier = getFieldValByName("updateBy", metaObject);
            Long userId = WebFrameworkUtils.getLoginUserId();
            if (Objects.nonNull(userId) && Objects.isNull(modifier)) {
                setFieldValByName("updateBy", userId.toString(), metaObject);
            }
        } else if (Objects.nonNull(metaObject) && metaObject.getOriginalObject() instanceof BaseEntity2) {//兼容旧代码
            // 更新时间为空，则以当前时间为更新时间
            setFieldValByName("updatedTime", LocalDateTime.now(), metaObject);

            // 当前登录用户不为空，更新人为空，则当前登录用户为更新人
            Object modifier = getFieldValByName("updatedBy", metaObject);
            Long userId = WebFrameworkUtils.getLoginUserId();
            if (Objects.nonNull(userId) && Objects.isNull(modifier)) {
                setFieldValByName("updatedBy", userId.toString(), metaObject);
            }
        }
    }
}
