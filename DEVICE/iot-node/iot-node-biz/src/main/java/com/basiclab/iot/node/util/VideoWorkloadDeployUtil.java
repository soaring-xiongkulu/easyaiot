package com.basiclab.iot.node.util;

import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * @deprecated 请使用 {@link WorkloadBundleDeployUtil}；保留兼容旧引用。
 */
@Deprecated
public final class VideoWorkloadDeployUtil {

    public static final String REMOTE_VIDEO_ROOT = WorkloadBundleDeployUtil.REMOTE_VIDEO_ROOT;

    private VideoWorkloadDeployUtil() {
    }

    public static boolean requiresVideoSync(String workloadType) {
        return WorkloadBundleDeployUtil.requiresVideoSync(workloadType);
    }

    public static List<String> syncRelativePaths(String workloadType) {
        WorkloadBundleTypeEnum bundle = WorkloadBundleDeployUtil.fromLegacyWorkloadType(workloadType);
        if (bundle == null) {
            String t = workloadType == null ? "" : workloadType.trim().toLowerCase(Locale.ROOT);
            if ("algorithm_task".equals(t)) {
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/realtime_algorithm_service",
                        "services/snapshot_algorithm_service"
                );
            }
            return Collections.emptyList();
        }
        return WorkloadBundleDeployUtil.syncScriptRelativePaths(bundle);
    }

    public static boolean shouldSkipDirectory(String name) {
        return WorkloadBundleDeployUtil.shouldSkipDirectory(name);
    }

    public static boolean shouldSkipFile(String name) {
        return WorkloadBundleDeployUtil.shouldSkipFile(name);
    }
}
