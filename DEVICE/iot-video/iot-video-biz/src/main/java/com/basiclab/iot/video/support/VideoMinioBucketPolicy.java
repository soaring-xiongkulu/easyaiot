package com.basiclab.iot.video.support;

/**
 * MinIO bucket public read/write policy aligned with Python {@code minio_bucket_policy}.
 */
public final class VideoMinioBucketPolicy {

    private VideoMinioBucketPolicy() {
    }

    public static String buildPublicReadWritePolicy(String bucketName) {
        return """
                {
                  "Version": "2012-10-17",
                  "Statement": [
                    {
                      "Effect": "Allow",
                      "Principal": {"AWS": ["*"]},
                      "Action": [
                        "s3:GetBucketLocation",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads"
                      ],
                      "Resource": ["arn:aws:s3:::%s"]
                    },
                    {
                      "Effect": "Allow",
                      "Principal": {"AWS": ["*"]},
                      "Action": [
                        "s3:ListMultipartUploadParts",
                        "s3:PutObject",
                        "s3:GetObject",
                        "s3:DeleteObject",
                        "s3:AbortMultipartUpload"
                      ],
                      "Resource": ["arn:aws:s3:::%s/*"]
                    }
                  ]
                }
                """.formatted(bucketName, bucketName);
    }
}
