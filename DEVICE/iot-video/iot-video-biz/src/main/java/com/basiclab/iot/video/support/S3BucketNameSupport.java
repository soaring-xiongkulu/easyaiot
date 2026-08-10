package com.basiclab.iot.video.support;

import com.basiclab.iot.video.exception.VideoBusinessException;

import java.util.regex.Pattern;

/**
 * S3 bucket naming validation — underscores and invalid chars cause MinIO 500;
 * return honest 4xx instead (Python {@code storage_service} uses hyphen buckets).
 */
public final class S3BucketNameSupport {

    private static final Pattern VALID = Pattern.compile("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$");

    private S3BucketNameSupport() {
    }

    public static void requireValid(String bucketName) {
        if (bucketName == null || bucketName.isBlank()) {
            throw new VideoBusinessException(400, "bucket_name 不能为空");
        }
        String name = bucketName.trim();
        if (name.contains("_")) {
            throw new VideoBusinessException(400,
                    "bucket_name 含非法字符 '_'（S3 命名不允许下划线）: " + name);
        }
        String lower = name.toLowerCase();
        if (!VALID.matcher(lower).matches()) {
            throw new VideoBusinessException(400, "bucket_name 不符合 S3 命名规则: " + name);
        }
    }
}
