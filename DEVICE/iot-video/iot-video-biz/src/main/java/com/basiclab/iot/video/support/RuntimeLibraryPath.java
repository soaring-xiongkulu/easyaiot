package com.basiclab.iot.video.support;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Build PATH (Windows) or LD_LIBRARY_PATH (Linux) for RUNTIME child processes.
 * Mirrors Python {@code runtime_config_service.runtime_library_path_env()}.
 */
public final class RuntimeLibraryPath {

    private RuntimeLibraryPath() {
    }

    public static String pathForProcess(Path repoRoot, Path runtimeBin) {
        if (isWindows()) {
            return buildWindowsPath(repoRoot, runtimeBin);
        }
        return buildLinuxPath(repoRoot);
    }

    private static boolean isWindows() {
        String os = System.getProperty("os.name", "").toLowerCase();
        return os.contains("win");
    }

    private static String buildWindowsPath(Path repoRoot, Path runtimeBin) {
        List<Path> candidates = new ArrayList<>();
        Path runtimeRoot = null;
        if (runtimeBin != null) {
            Path binDir = runtimeBin.getParent();
            if (binDir != null) {
                candidates.add(binDir);
                runtimeRoot = binDir.getParent();
                if (runtimeRoot != null && "build-win".equalsIgnoreCase(String.valueOf(runtimeRoot.getFileName()))) {
                    runtimeRoot = runtimeRoot.getParent();
                } else if (runtimeRoot != null && "Release".equalsIgnoreCase(String.valueOf(binDir.getFileName()))) {
                    runtimeRoot = runtimeRoot.getParent();
                    if (runtimeRoot != null && "build-win".equalsIgnoreCase(String.valueOf(runtimeRoot.getFileName()))) {
                        runtimeRoot = runtimeRoot.getParent();
                    }
                }
            }
        }
        if (runtimeRoot != null) {
            Path vendor = runtimeRoot.resolve("vendor");
            candidates.add(vendor.resolve("conda-env/Library/bin"));
            Path condaPkgs = vendor.resolve("win-x64/conda-pkgs");
            candidates.add(condaPkgs.resolve("libprotobuf/Library/bin"));
            candidates.add(condaPkgs.resolve("opencv/Library/bin"));
            candidates.add(condaPkgs.resolve("ffmpeg/Library/bin"));
            candidates.add(condaPkgs.resolve("jsoncpp/Library/bin"));
            candidates.add(condaPkgs.resolve("ffmpeg4/Library/bin"));
            candidates.add(vendor.resolve("win-x64/_conda_ffmpeg4/Library/bin"));
            candidates.add(vendor.resolve("onnxruntime/lib"));
        }
        if (repoRoot != null) {
            Path runtimeFromRepo = repoRoot.resolve("RUNTIME");
            candidates.add(runtimeFromRepo.resolve("build-win/Release"));
            Path vendor = runtimeFromRepo.resolve("vendor");
            candidates.add(vendor.resolve("conda-env/Library/bin"));
            Path condaPkgs = vendor.resolve("win-x64/conda-pkgs");
            candidates.add(condaPkgs.resolve("libprotobuf/Library/bin"));
            candidates.add(condaPkgs.resolve("opencv/Library/bin"));
            candidates.add(condaPkgs.resolve("ffmpeg/Library/bin"));
            candidates.add(condaPkgs.resolve("jsoncpp/Library/bin"));
            candidates.add(condaPkgs.resolve("ffmpeg4/Library/bin"));
            candidates.add(vendor.resolve("win-x64/_conda_ffmpeg4/Library/bin"));
            candidates.add(vendor.resolve("onnxruntime/lib"));
        }
        String condaPrefix = System.getenv("CONDA_PREFIX");
        if (condaPrefix != null && !condaPrefix.isBlank()) {
            candidates.add(Path.of(condaPrefix.trim(), "Library", "bin"));
        }
        for (String guess : List.of(
                "F:/anaconda/Library/bin",
                System.getenv("USERPROFILE") + "/anaconda3/Library/bin",
                System.getenv("USERPROFILE") + "/miniconda3/Library/bin",
                "C:/ProgramData/anaconda3/Library/bin"
        )) {
            if (guess != null && !guess.contains("null")) {
                candidates.add(Path.of(guess));
            }
        }
        return joinExisting(candidates, System.getenv("PATH"));
    }

    private static String buildLinuxPath(Path repoRoot) {
        List<Path> candidates = new ArrayList<>();
        String existing = System.getenv("LD_LIBRARY_PATH");
        if (existing != null && !existing.isBlank()) {
            for (String part : existing.split(":")) {
                candidates.add(Path.of(part));
            }
        }
        for (String mounted : List.of(
                "/opt/easyaiot/runtime-conda-lib",
                "/opt/easyaiot/ort-lib",
                "/opt/easyaiot/cuda-lib"
        )) {
            candidates.add(Path.of(mounted));
        }
        String condaPrefix = System.getenv("CONDA_PREFIX");
        if (condaPrefix != null && !condaPrefix.isBlank()) {
            candidates.add(Path.of(condaPrefix.trim(), "lib"));
        }
        if (repoRoot != null) {
            candidates.add(repoRoot.resolve("RUNTIME/build/lib"));
            candidates.add(repoRoot.resolve("RUNTIME/vendor/onnxruntime/lib"));
        }
        return joinExisting(candidates, null);
    }

    private static String joinExisting(List<Path> candidates, String trailing) {
        Set<String> seen = new LinkedHashSet<>();
        List<String> out = new ArrayList<>();
        for (Path candidate : candidates) {
            if (candidate == null) {
                continue;
            }
            String normalized = candidate.toString();
            if (Files.isDirectory(candidate) && seen.add(normalized)) {
                out.add(normalized);
            }
        }
        if (trailing != null && !trailing.isBlank()) {
            out.add(trailing);
        }
        return String.join(isWindows() ? ";" : ":", out);
    }
}
