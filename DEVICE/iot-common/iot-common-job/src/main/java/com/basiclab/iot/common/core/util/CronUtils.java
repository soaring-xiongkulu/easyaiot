package com.basiclab.iot.common.core.util;

import cn.hutool.core.date.LocalDateTimeUtil;
import org.quartz.CronExpression;

import java.text.ParseException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * Quartz Cron 表达式的工具类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public class CronUtils {

    /**
     * 校验 CRON 表达式是否有效
     *
     * @param cronExpression CRON 表达式
     * @return 是否有效
     */
    public static boolean isValid(String cronExpression) {
        return CronExpression.isValidExpression(cronExpression);
    }

    /**
     * 基于 CRON 表达式，获得下 n 个满足执行的时间
     *
     * @param cronExpression CRON 表达式
     * @param n 数量
     * @return 满足条件的执行时间
     */
    public static List<LocalDateTime> getNextTimes(String cronExpression, int n) {
        // 获得 CronExpression 对象
        CronExpression cron;
        try {
            cron = new CronExpression(cronExpression);
        } catch (ParseException e) {
            throw new IllegalArgumentException(e.getMessage());
        }
        // 从当前开始计算，n 个满足条件的
        Date now = new Date();
        List<LocalDateTime> nextTimes = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            Date nextTime = cron.getNextValidTimeAfter(now);
            nextTimes.add(LocalDateTimeUtil.of(nextTime));
            // 切换现在，为下一个触发时间；
            now = nextTime;
        }
        return nextTimes;
    }


    /**
     * 返回下一个执行时间根据给定的Cron表达式
     *
     * @param cronExpression Cron表达式
     * @return Date 下次Cron表达式执行时间
     */
    public static Date getNextExecution(String cronExpression)
    {
        try
        {
            CronExpression cron = new CronExpression(cronExpression);
            return cron.getNextValidTimeAfter(new Date(System.currentTimeMillis()));
        }
        catch (ParseException e)
        {
            throw new IllegalArgumentException(e.getMessage());
        }
    }
}
