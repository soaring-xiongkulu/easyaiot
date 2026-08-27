package com.basiclab.iot.node.util;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RecordingStorageMountUtilTest {

    @Test
    void acceptsNetworkAndClusterFilesystems() {
        assertTrue(RecordingStorageMountUtil.isSharedFilesystemType("nfs4"));
        assertTrue(RecordingStorageMountUtil.isSharedFilesystemType("ceph"));
        assertTrue(RecordingStorageMountUtil.isSharedFilesystemType("fuse.glusterfs"));
    }

    @Test
    void rejectsWritableLocalFilesystems() {
        assertFalse(RecordingStorageMountUtil.isSharedFilesystemType("ext4"));
        assertFalse(RecordingStorageMountUtil.isSharedFilesystemType("xfs"));
        assertFalse(RecordingStorageMountUtil.isSharedFilesystemType("overlay"));
        assertFalse(RecordingStorageMountUtil.isSharedFilesystemType(""));
    }
}
