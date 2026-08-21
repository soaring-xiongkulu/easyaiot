package com.basiclab.iot.node.util;

import com.basiclab.iot.node.enums.WorkloadBundleTypeEnum;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * 计算节点工作负载分发：脚本路径、离线运行时、远程目录。
 * 默认目标机无外网，运行时经 pip-wheels 离线安装。
 */
public final class WorkloadBundleDeployUtil {

    public static final String REMOTE_VIDEO_ROOT = "/opt/easyaiot/VIDEO";
    public static final String REMOTE_AI_ROOT = "/opt/easyaiot/AI";
    public static final String REMOTE_TRANSFORM_ROOT = "/opt/easyaiot/TRANSFORM";
    public static final String REMOTE_LIB_ROOT = "/opt/easyaiot/lib";
    public static final String BUNDLE_SUBDIR = ".bundles";
    public static final String PIP_WHEELS_DIR = "pip-wheels";
    public static final String EXPORT_PIP_WHEELS_SCRIPT = "export_node_pip_wheels.sh";
    public static final String INSTALL_BUNDLE_ENV_SCRIPT = "install_node_bundle_env.sh";
    public static final String GET_PIP_SCRIPT = "get-pip.py";
    public static final String RUN_PYTHON_LAUNCHER = "run-python.sh";
    public static final String WHEELS_TARGET_MARKER = ".target-python";
    public static final String WHEELS_META_FILE = ".bundle-meta";

    private static final Set<String> SKIP_DIR_NAMES = new HashSet<>(Arrays.asList(
            "__pycache__", ".git", "logs", "node_modules", ".venv", "venv", ".bundle-wheels", BUNDLE_SUBDIR
    ));

    private static final Set<String> SKIP_FILE_SUFFIXES = new HashSet<>(Arrays.asList(
            ".pyc", ".pyo"
    ));

    private WorkloadBundleDeployUtil() {
    }

    public static String moduleRoot(WorkloadBundleTypeEnum bundle) {
        if ("TRANSFORM".equals(bundle.getModule())) {
            return REMOTE_TRANSFORM_ROOT;
        }
        return "AI".equals(bundle.getModule()) ? REMOTE_AI_ROOT : REMOTE_VIDEO_ROOT;
    }

    /** 远程 bundle 运行时目录，如 /opt/easyaiot/VIDEO/.bundles/stream_forward */
    public static String remoteBundleDir(WorkloadBundleTypeEnum bundle) {
        return moduleRoot(bundle) + "/" + BUNDLE_SUBDIR + "/" + bundle.getType();
    }

    public static String remotePythonLauncher(WorkloadBundleTypeEnum bundle) {
        return remoteBundleDir(bundle) + "/" + RUN_PYTHON_LAUNCHER;
    }

    /**
     * 展开 {@code -r} 引用，生成节点上可独立安装的 requirements.txt。
     * 算法 bundle 依赖 stream-forward 等文件，原样上传会导致 pip 在 bundle 目录找不到被引用文件。
     */
    public static String flattenRequirements(File reqFile) throws IOException {
        if (reqFile == null || !reqFile.isFile()) {
            throw new IOException("requirements 不存在: " + reqFile);
        }
        return flattenRequirements(reqFile, new HashSet<>());
    }

    private static String flattenRequirements(File reqFile, Set<String> seen) throws IOException {
        String canonical = reqFile.getCanonicalPath();
        if (!seen.add(canonical)) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        for (String line : Files.readAllLines(reqFile.toPath(), StandardCharsets.UTF_8)) {
            String trimmed = line.trim();
            if (trimmed.startsWith("-r ")) {
                String ref = trimmed.substring(3).trim();
                File inc = new File(reqFile.getParentFile(), ref);
                if (!inc.isFile()) {
                    throw new IOException("requirements 引用缺失: " + inc);
                }
                sb.append(flattenRequirements(inc, seen));
                continue;
            }
            if (trimmed.startsWith("--requirement ")) {
                String ref = trimmed.substring("--requirement ".length()).trim();
                File inc = new File(reqFile.getParentFile(), ref);
                if (!inc.isFile()) {
                    throw new IOException("requirements 引用缺失: " + inc);
                }
                sb.append(flattenRequirements(inc, seen));
                continue;
            }
            sb.append(line).append('\n');
        }
        return sb.toString();
    }

    public static String requirementsFileName(WorkloadBundleTypeEnum bundle) {
        switch (bundle) {
            case STREAM_FORWARD:
                return "requirements-node-stream-forward.txt";
            case ALGORITHM_REALTIME:
                return "requirements-node-algorithm-realtime.txt";
            case ALGORITHM_SNAP:
                return "requirements-node-algorithm-snap.txt";
            case ALGORITHM_PATROL:
                return "requirements-node-algorithm-patrol.txt";
            case AI_SERVICE:
                return "requirements-node-ai-service.txt";
            case LLM_SERVICE:
                return "requirements-node-llm-service.txt";
            case MODEL_TRAIN:
                return "requirements-node-model-train.txt";
            case POST_PROCESS:
                return "requirements-node-post-process.txt";
            case TRANSFORM_RUNTIME:
                // Java runtime：无 pip requirements
                return "";
            default:
                throw new IllegalArgumentException("unknown bundle: " + bundle);
        }
    }

    public static boolean isJavaRuntimeBundle(WorkloadBundleTypeEnum bundle) {
        return bundle == WorkloadBundleTypeEnum.TRANSFORM_RUNTIME;
    }

    public static String localWheelsCacheDir(
            String sourceRoot, WorkloadBundleTypeEnum bundle,
            String osFamily, String archKey, String targetPython) {
        return sourceRoot + "/.bundle-wheels/"
                + bundle.getType() + "/"
                + normalizeTargetKey(osFamily, "linux") + "/"
                + normalizeTargetKey(archKey, "x86_64") + "/"
                + pythonCacheKey(targetPython);
    }

    /**
     * 旧布局：仅 bundleType。只有控制面本机与目标节点 OS/arch 一致时才允许回退，避免跨 ABI 混包。
     */
    public static String legacyLocalWheelsCacheDir(String sourceRoot, WorkloadBundleTypeEnum bundle) {
        return sourceRoot + "/.bundle-wheels/" + bundle.getType();
    }

    /** 需同步的源码相对路径（相对模块根目录） */
    public static List<String> syncScriptRelativePaths(WorkloadBundleTypeEnum bundle) {
        switch (bundle) {
            case STREAM_FORWARD:
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/stream_forward_service"
                );
            case ALGORITHM_REALTIME:
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/realtime_algorithm_service"
                );
            case ALGORITHM_SNAP:
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/snapshot_algorithm_service"
                );
            case ALGORITHM_PATROL:
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/patrol_algorithm_service"
                );
            case AI_SERVICE:
                return Arrays.asList(
                        "db_models.py",
                        "app",
                        "services/ai_service"
                );
            case LLM_SERVICE:
                return Arrays.asList(
                        "db_models.py",
                        "app/config/qwen_models.py",
                        "app",
                        "services/llm_service"
                );
            case AUTO_LABEL:
                return syncAutoLabelRelativePaths();
            case MODEL_TRAIN:
                return syncModelTrainRelativePaths();
            case POST_PROCESS:
                return Arrays.asList(
                        "models.py",
                        "app",
                        "services/post_process_worker"
                );
            case TRANSFORM_RUNTIME:
                return Arrays.asList(
                        "Dockerfile",
                        "scripts/run-runtime.sh",
                        "scripts/run-runtime-container.sh",
                        "scripts/run-multi-containers.sh",
                        "scripts/agent-deploy-containers.sh",
                        "scripts/build-image.sh",
                        "scripts/pipeline-distribute-run.sh",
                        "scripts/wait-heartbeat.py",
                        "transform-runtime/target/transform-runtime-1.0.0.jar",
                        "dist/transform-runtime-1.0.0.tar.gz",
                        "dist/transform-runtime-1.0.0.tar"
                );
            default:
                return Collections.emptyList();
        }
    }

    /** 检测脚本是否就绪的标记文件（相对模块根） */
    public static String scriptReadyMarker(WorkloadBundleTypeEnum bundle) {
        switch (bundle) {
            case STREAM_FORWARD:
                return "services/stream_forward_service/run_deploy.py";
            case ALGORITHM_REALTIME:
                return "services/realtime_algorithm_service/run_deploy.py";
            case ALGORITHM_SNAP:
                return "services/snapshot_algorithm_service/run_deploy.py";
            case ALGORITHM_PATROL:
                return "services/patrol_algorithm_service/run_deploy.py";
            case AI_SERVICE:
                return "services/ai_service/run_deploy.py";
            case LLM_SERVICE:
                return "services/llm_service/run_deploy.py";
            case AUTO_LABEL:
                return "services/auto_label_worker/run_worker.py";
            case MODEL_TRAIN:
                return "services/train_worker/run_worker.py";
            case POST_PROCESS:
                return "services/post_process_worker/run_worker.py";
            case TRANSFORM_RUNTIME:
                return "scripts/run-runtime.sh";
            default:
                return "";
        }
    }

    public static String sourceRootMarker(WorkloadBundleTypeEnum bundle) {
        if ("TRANSFORM".equals(bundle.getModule())) {
            return "pom.xml";
        }
        return "AI".equals(bundle.getModule()) ? "db_models.py" : "models.py";
    }

    /** 离线 import 验证命令 */
    public static String verifyImportCommand(WorkloadBundleTypeEnum bundle, String launcher) {
        switch (bundle) {
            case STREAM_FORWARD:
                return launcher + " -c \"import cv2, flask, sqlalchemy, requests; print('OK')\"";
            case ALGORITHM_REALTIME:
            case ALGORITHM_SNAP:
            case ALGORITHM_PATROL:
                return launcher + " -c \"import cv2, flask, sqlalchemy, onnxruntime; print('OK')\"";
            case AI_SERVICE:
                return launcher + " -c \"import flask, cv2, numpy, onnxruntime; print('OK')\"";
            case LLM_SERVICE:
                return launcher + " -c \"import vllm, transformers; print('OK')\"";
            case MODEL_TRAIN:
                return launcher + " -c \"import torch, ultralytics, yaml; print('OK')\"";
            case POST_PROCESS:
                return launcher + " -c \"import flask, sqlalchemy, kafka; print('OK')\"";
            case TRANSFORM_RUNTIME:
                return "test -f /opt/easyaiot/TRANSFORM/scripts/run-runtime-container.sh "
                        + "&& (docker image inspect easyaiot/transform-runtime:1.0.0 >/dev/null 2>&1 "
                        + "|| test -f /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar.gz "
                        + "|| test -f /opt/easyaiot/TRANSFORM/dist/transform-runtime-1.0.0.tar) "
                        + "&& echo OK";
            default:
                return launcher + " -c \"print('OK')\"";
        }
    }

    public static boolean shouldSkipDirectory(String name) {
        return name == null || name.isEmpty() || SKIP_DIR_NAMES.contains(name);
    }

    public static boolean shouldSkipFile(String name) {
        if (name == null || name.isEmpty()) {
            return true;
        }
        if (".env".equals(name) || ".env.prod".equals(name) || ".env.docker".equals(name)) {
            return true;
        }
        for (String suffix : SKIP_FILE_SUFFIXES) {
            if (name.endsWith(suffix)) {
                return true;
            }
        }
        return false;
    }

    /** 兼容旧 workloadType 到 bundle */
    public static WorkloadBundleTypeEnum fromLegacyWorkloadType(String workloadType) {
        if (workloadType == null) {
            return null;
        }
        String t = workloadType.trim().toLowerCase(Locale.ROOT);
        if ("stream_forward".equals(t)) {
            return WorkloadBundleTypeEnum.STREAM_FORWARD;
        }
        if ("algorithm_task".equals(t)) {
            return WorkloadBundleTypeEnum.ALGORITHM_REALTIME;
        }
        if ("ai_service".equals(t)) {
            return WorkloadBundleTypeEnum.AI_SERVICE;
        }
        return WorkloadBundleTypeEnum.of(t);
    }

    public static boolean requiresVideoSync(String workloadType) {
        WorkloadBundleTypeEnum b = fromLegacyWorkloadType(workloadType);
        return b != null && "VIDEO".equals(b.getModule());
    }

    public static boolean requiresAiSync(String workloadType) {
        String t = workloadType == null ? "" : workloadType.trim().toLowerCase(Locale.ROOT);
        return WorkloadBundleTypeEnum.AI_SERVICE.getType().equals(t)
                || WorkloadBundleTypeEnum.LLM_SERVICE.getType().equals(t)
                || WorkloadBundleTypeEnum.AUTO_LABEL.getType().equals(t)
                || WorkloadBundleTypeEnum.MODEL_TRAIN.getType().equals(t);
    }

    /** 自动标注 Worker 需同步的源码路径（相对 AI 根目录） */
    public static List<String> syncAutoLabelRelativePaths() {
        return Arrays.asList(
                "db_models.py",
                "app",
                "services/auto_label_worker"
        );
    }

    /** 模型训练 Worker 需同步的源码路径（相对 AI 根目录） */
    public static List<String> syncModelTrainRelativePaths() {
        return Arrays.asList(
                "db_models.py",
                "run.py",
                "app",
                "services/train_worker"
        );
    }

    public static String pythonCacheKey(String targetPython) {
        String normalized = normalizePythonVersion(targetPython);
        return "py" + normalized.replace(".", "");
    }

    public static String normalizePythonVersion(String targetPython) {
        if (targetPython == null || targetPython.isBlank()) {
            return "3.10";
        }
        String normalized = targetPython.trim().toLowerCase(Locale.ROOT).replace("cp", "");
        String[] parts = normalized.split("\\.");
        if (parts.length >= 2 && parts[0].matches("\\d+") && parts[1].matches("\\d+")) {
            return parts[0] + "." + parts[1];
        }
        return "3.10";
    }

    private static String normalizeTargetKey(String raw, String fallback) {
        if (raw == null || raw.isBlank()) {
            return fallback;
        }
        String normalized = raw.trim().toLowerCase(Locale.ROOT).replaceAll("[^a-z0-9._-]", "-");
        return normalized.isEmpty() ? fallback : normalized;
    }
}
