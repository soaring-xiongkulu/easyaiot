package com.basiclab.iot.common.mybatis.core.enums;

import com.baomidou.mybatisplus.annotation.DbType;

/**
 * SQL相关常量类
 *
 * @author 安徽上洲智能科技
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
