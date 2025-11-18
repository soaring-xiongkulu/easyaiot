package com.basiclab.iot.infra.controller.admin.redis.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.util.List;
import java.util.Properties;

/**
 * RedisMonitorRespVO
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Schema(description = "管理后台 - Redis 监控信息 Response VO")
@Data
@Builder
@AllArgsConstructor
public class RedisMonitorRespVO {

    @Schema(description = "Redis info 指令结果,具体字段，查看 Redis 文档")
    private Properties info;

    @Schema(description = "Redis key 数量", example = "1024")
    private Long dbSize;

    @Schema(description = "CommandStat 数组")
    private List<CommandStat> commandStats;

    @Schema(description = "Redis 命令统计结果")
    @Data
    @Builder
    @AllArgsConstructor
    public static class CommandStat {

        @Schema(description = "Redis 命令", example = "get")
        private String command;

        @Schema(description = "调用次数", example = "1024")
        private Long calls;

        @Schema(description = "消耗 CPU 秒数", example = "666")
        private Long usec;

    }

}
