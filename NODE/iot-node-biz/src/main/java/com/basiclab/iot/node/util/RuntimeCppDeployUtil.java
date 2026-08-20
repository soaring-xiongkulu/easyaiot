package com.basiclab.iot.node.util;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.Locale;

/**
 * RUNTIME（C++ 高性能算法执行器）离线分发工具。
 * 控制面按 {osFamily}/{arch} 缓存 tarball → SSH 同步 → 节点 install_runtime_cpp.sh。
 * 禁止把本机 Ubuntu 编的包发到 openEuler / EL 等不同 ABI。
 */
public final class RuntimeCppDeployUtil {

    public static final String REMOTE_RUNTIME_ROOT = "/opt/easyaiot/RUNTIME";
    public static final String REMOTE_RUNTIME_BIN = REMOTE_RUNTIME_ROOT + "/bin/RUNTIME";
    public static final String REMOTE_RUNTIME_LIB = REMOTE_RUNTIME_ROOT + "/lib";
    public static final String REMOTE_RUNTIME_CONFIG = REMOTE_RUNTIME_ROOT + "/config";
    public static final String REMOTE_RUNTIME_VERSION = REMOTE_RUNTIME_ROOT + "/VERSION";
    public static final String REMOTE_SMOKE_SCRIPT = REMOTE_RUNTIME_ROOT + "/scripts/smoke_runtime.sh";
    public static final String REMOTE_CACHE_SUBDIR = "cache";

    public static final String EXPORT_SCRIPT = "export_runtime_cpp.sh";
    public static final String EXPORT_OS_CONTAINER_SCRIPT = "scripts/export_runtime_os_container.sh";
    public static final String EXPORT_ALL_SCRIPT = "scripts/export_runtime_all.sh";
    public static final String PREFLIGHT_SCRIPT = "scripts/preflight_runtime_bundle.sh";
    public static final String INSTALL_SCRIPT = "install_runtime_cpp.sh";

    private RuntimeCppDeployUtil() {
    }

    public static final class OsArch {
        public final String osFamily;
        public final String archKey;
        public final String osId;
        public final String versionId;
        public final String uname;

        public OsArch(String osFamily, String archKey, String osId, String versionId, String uname) {
            this.osFamily = osFamily;
            this.archKey = archKey;
            this.osId = osId;
            this.versionId = versionId;
            this.uname = uname;
        }

        public String bundleKey() {
            return osFamily + "/" + archKey;
        }
    }

    public static String localCacheDir(String runtimeSourceRoot, String osFamily, String archKey) {
        return runtimeSourceRoot + "/.bundle-runtime/" + osFamily + "/" + archKey;
    }

    /** 旧布局：仅 arch。仅当目标 OS 与控制面本机相同时才允许回退。 */
    public static String legacyCacheDir(String runtimeSourceRoot, String archKey) {
        return runtimeSourceRoot + "/.bundle-runtime/" + archKey;
    }

    public static String tarballName(String osFamily, String archKey) {
        return "easyaiot-runtime-" + osFamily + "-" + archKey + ".tar.gz";
    }

    public static String legacyTarballName(String archKey) {
        return "easyaiot-runtime-" + archKey + ".tar.gz";
    }

    public static String archKeyForUname(String unameMachine) {
        String m = unameMachine == null ? "" : unameMachine.trim().toLowerCase(Locale.ROOT);
        if (m.contains("aarch64") || m.contains("arm64")) {
            return "arm64";
        }
        return "x86_64";
    }

    public static String exportArchEnv(String archKey) {
        return "arm64".equals(archKey) ? "arm64" : "x86_64";
    }

    public static String detectLocalArchKey() {
        return archKeyForUname(System.getProperty("os.arch", ""));
    }

    public static String detectOsReleaseCommand() {
        return "bash -c '. /etc/os-release 2>/dev/null; "
                + "printf \"ID=%s\\nID_LIKE=%s\\nVERSION_ID=%s\\nUNAME=%s\\n\" "
                + "\"${ID:-}\" \"${ID_LIKE:-}\" \"${VERSION_ID:-}\" \"$(uname -m)\"'";
    }

    public static OsArch parseOsArch(String detectOutput) {
        String id = "";
        String like = "";
        String versionId = "";
        String uname = "x86_64";
        if (detectOutput != null) {
            for (String raw : detectOutput.split("\\R")) {
                String line = raw.trim();
                int idx = line.indexOf('=');
                if (idx <= 0) {
                    continue;
                }
                String key = line.substring(0, idx).trim();
                String value = unquote(line.substring(idx + 1).trim());
                if ("ID".equals(key)) {
                    id = value;
                } else if ("ID_LIKE".equals(key)) {
                    like = value;
                } else if ("VERSION_ID".equals(key)) {
                    versionId = value;
                } else if ("UNAME".equals(key)) {
                    uname = value;
                }
            }
        }
        String arch = archKeyForUname(uname);
        String family = osFamilyFrom(id, like, versionId);
        return new OsArch(family, arch, id, versionId, uname);
    }

    public static String detectLocalOsFamily() {
        File file = new File("/etc/os-release");
        if (!file.isFile()) {
            return osFamilyFrom("", "", "");
        }
        String id = "";
        String like = "";
        String versionId = "";
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                int idx = line.indexOf('=');
                if (idx <= 0) {
                    continue;
                }
                String key = line.substring(0, idx).trim();
                String value = unquote(line.substring(idx + 1).trim());
                switch (key) {
                    case "ID":
                        id = value;
                        break;
                    case "ID_LIKE":
                        like = value;
                        break;
                    case "VERSION_ID":
                        versionId = value;
                        break;
                    default:
                        break;
                }
            }
        } catch (Exception ignored) {
            // fall through to empty mapping
        }
        return osFamilyFrom(id, like, versionId);
    }

    public static String osFamilyFrom(String id, String idLike, String versionId) {
        String distro = normalizeId(id);
        String like = normalizeId(idLike);
        int major = majorVersion(versionId);

        if ("ubuntu".equals(distro)) {
            return major > 0 ? "ubuntu" + major : "ubuntu";
        }
        if ("debian".equals(distro)) {
            return major > 0 ? "debian" + major : "debian";
        }
        if ("openeuler".equals(distro)) {
            return major > 0 ? "openeuler" + major : "openeuler";
        }
        if (distro.contains("kylin")) {
            return major > 0 ? "kylin" + major : "kylin";
        }
        if (isNamedEl(distro)) {
            return elFamily(major);
        }
        // openEuler / Kylin 已在前面处理；其余 ID_LIKE=rhel 归入 el
        if (like.contains("rhel") || like.contains("centos") || like.contains("fedora")) {
            return elFamily(major);
        }
        if (!distro.isEmpty()) {
            String slug = distro.replaceAll("[^a-z0-9]", "");
            return major > 0 ? slug + major : slug;
        }
        return "linux";
    }

    public static String missingBundleHint(String osFamily, String archKey) {
        String name = tarballName(osFamily, archKey);
        return "控制面缺少 RUNTIME 包 os=" + osFamily + " arch=" + archKey
                + "。请在对应 OS 容器内编译并导出（与 COMPILE 矩阵对齐）：\n"
                + "  bash RUNTIME/" + EXPORT_OS_CONTAINER_SCRIPT + " " + osFamily + "\n"
                + "或批量：\n"
                + "  bash RUNTIME/" + EXPORT_ALL_SCRIPT + " --compile-target all-linux\n"
                + "分发前预检：\n"
                + "  bash RUNTIME/" + PREFLIGHT_SCRIPT + " " + osFamily + " " + archKey + "\n"
                + "产物应落到：\n"
                + "  RUNTIME/.bundle-runtime/" + osFamily + "/" + archKey + "/" + name + "\n"
                + "不要把本机 Ubuntu 包发到该节点。";
    }

    /** 查找已就绪的本地 tarball（含同 ABI 旧布局回退）。 */
    public static File findLocalTarball(String runtimeSourceRoot, OsArch target) {
        if (runtimeSourceRoot == null || runtimeSourceRoot.isBlank() || target == null) {
            return null;
        }
        File cacheDir = new File(localCacheDir(runtimeSourceRoot, target.osFamily, target.archKey));
        File tar = new File(cacheDir, tarballName(target.osFamily, target.archKey));
        if (isUsableTarball(tar)) {
            return tar;
        }
        String localOs = detectLocalOsFamily();
        String localArch = detectLocalArchKey();
        if (target.osFamily.equals(localOs) && target.archKey.equals(localArch)) {
            File legacy = new File(legacyCacheDir(runtimeSourceRoot, target.archKey),
                    legacyTarballName(target.archKey));
            if (isUsableTarball(legacy)) {
                return legacy;
            }
        }
        return null;
    }

    public static boolean isUsableTarball(File tar) {
        return tar != null && tar.isFile() && tar.length() > 1024L;
    }

    /**
     * 文件存在不算就绪：必须 source env.sh 后能跑 --version。
     */
    public static String verifyCommand() {
        return "bash -c '"
                + "if [ ! -x " + REMOTE_RUNTIME_BIN + " ]; then echo RUNTIME_MISSING; exit 0; fi; "
                + "if [ -f " + REMOTE_RUNTIME_VERSION + " ]; then "
                + "echo ---VERSION_BEGIN---; cat " + REMOTE_RUNTIME_VERSION + "; echo ---VERSION_END---; fi; "
                + "if [ -f " + REMOTE_SMOKE_SCRIPT + " ]; then "
                + "if bash " + REMOTE_SMOKE_SCRIPT + " " + REMOTE_RUNTIME_ROOT + "; then echo RUNTIME_OK; "
                + "else echo RUNTIME_SMOKE_FAIL; fi; "
                + "else "
                + "unset LD_LIBRARY_PATH LD_PRELOAD; "
                + "[ -f " + REMOTE_RUNTIME_ROOT + "/env.sh ] && . " + REMOTE_RUNTIME_ROOT + "/env.sh; "
                + "if " + REMOTE_RUNTIME_BIN + " --version >/dev/null 2>&1; then echo RUNTIME_OK; "
                + "else echo RUNTIME_EXEC_FAIL; " + REMOTE_RUNTIME_BIN + " --version; fi; "
                + "fi"
                + "'";
    }

    public static boolean outputMeansReady(String combinedOutput) {
        if (combinedOutput == null) {
            return false;
        }
        if (combinedOutput.contains("RUNTIME_MISSING")
                || combinedOutput.contains("RUNTIME_SMOKE_FAIL")
                || combinedOutput.contains("RUNTIME_EXEC_FAIL")
                || combinedOutput.contains("SMOKE_FAIL")) {
            return false;
        }
        return combinedOutput.contains("RUNTIME_OK") || combinedOutput.contains("SMOKE_OK");
    }

    public static String remoteLdLibraryPath() {
        return REMOTE_RUNTIME_LIB
                + ":/usr/local/cuda/lib64:/usr/local/cuda/lib"
                + ":/usr/lib/x86_64-linux-gnu:/usr/lib/aarch64-linux-gnu";
    }

    /** 从 VERSION 文本解析 key=value。 */
    public static java.util.Map<String, String> parseVersionText(String text) {
        java.util.Map<String, String> map = new java.util.LinkedHashMap<>();
        if (text == null || text.isBlank()) {
            return map;
        }
        for (String line : text.split("\\R")) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("#")) {
                continue;
            }
            int idx = trimmed.indexOf('=');
            if (idx <= 0) {
                continue;
            }
            String key = trimmed.substring(0, idx).trim();
            String value = trimmed.substring(idx + 1).trim();
            if (!key.isEmpty()) {
                map.put(key, value);
            }
        }
        return map;
    }

    public static String extractVersionBlock(String combinedOutput) {
        if (combinedOutput == null) {
            return "";
        }
        int begin = combinedOutput.indexOf("---VERSION_BEGIN---");
        int end = combinedOutput.indexOf("---VERSION_END---");
        if (begin >= 0 && end > begin) {
            return combinedOutput.substring(begin + "---VERSION_BEGIN---".length(), end).trim();
        }
        return "";
    }

    private static String normalizeId(String raw) {
        if (raw == null) {
            return "";
        }
        return unquote(raw).trim().toLowerCase(Locale.ROOT);
    }

    private static String unquote(String value) {
        if (value == null) {
            return "";
        }
        String v = value.trim();
        if (v.length() >= 2) {
            char first = v.charAt(0);
            char last = v.charAt(v.length() - 1);
            if ((first == '"' && last == '"') || (first == '\'' && last == '\'')) {
                return v.substring(1, v.length() - 1);
            }
        }
        return v;
    }

    private static int majorVersion(String versionId) {
        String v = unquote(versionId);
        if (v.isEmpty()) {
            return 0;
        }
        int i = 0;
        while (i < v.length() && Character.isDigit(v.charAt(i))) {
            i++;
        }
        if (i == 0) {
            return 0;
        }
        try {
            return Integer.parseInt(v.substring(0, i));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static boolean isNamedEl(String distro) {
        return "rhel".equals(distro)
                || "centos".equals(distro)
                || "rocky".equals(distro)
                || "almalinux".equals(distro)
                || "ol".equals(distro)
                || "alinux".equals(distro)
                || "opencloudos".equals(distro)
                || "anolis".equals(distro)
                || "tencentos".equals(distro);
    }

    private static String elFamily(int major) {
        if (major >= 9) {
            return "el9";
        }
        if (major == 8) {
            return "el8";
        }
        if (major == 7) {
            return "el7";
        }
        return "el";
    }
}
