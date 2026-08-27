package com.basiclab.iot.node.util;

import java.util.Locale;
import java.util.Set;

/** 录像共享存储挂载类型判定。 */
public final class RecordingStorageMountUtil {

    private static final Set<String> SHARED_FILESYSTEM_TYPES = Set.of(
            "nfs", "nfs4", "ceph", "fuse.ceph", "cifs", "smb3",
            "glusterfs", "fuse.glusterfs", "lustre", "gpfs");

    private RecordingStorageMountUtil() {
    }

    public static boolean isSharedFilesystemType(String fsType) {
        if (fsType == null) {
            return false;
        }
        return SHARED_FILESYSTEM_TYPES.contains(fsType.trim().toLowerCase(Locale.ROOT));
    }
}
