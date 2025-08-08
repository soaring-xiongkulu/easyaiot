package com.basiclab.iot.common.core.enums;

import com.baomidou.mybatisplus.annotation.DbType;

/**
 * SQL相关常量类
 *
 * @author IoT
 */
public class SqlConstants {

    /**
     * 数据库的类型
     */
    public static DbType DB_TYPE;

    public static void init(DbType dbType) {
        DB_TYPE = dbType;
    }

}
