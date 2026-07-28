package com.basiclab.iot.dataset.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executor;

@Component
public class DatasetSyncTaskManager {

    private static final Logger logger = LoggerFactory.getLogger(DatasetSyncTaskManager.class);

    private final Executor executor;
    private final Set<Long> syncingDatasetIds = ConcurrentHashMap.newKeySet();
    private final ConcurrentHashMap<Long, TaskSnapshot> snapshots = new ConcurrentHashMap<>();

    public DatasetSyncTaskManager(@Qualifier("datasetSyncExecutor") Executor executor) {
        this.executor = executor;
    }

    public boolean submit(Long datasetId, Runnable task) {
        return submit(datasetId, null, task);
    }

    public boolean submit(Long datasetId, Integer totalImages, Runnable task) {
        if (!syncingDatasetIds.add(datasetId)) {
            return false;
        }
        snapshots.put(datasetId, new TaskSnapshot(
                SyncStatus.QUEUED, SyncStage.WAITING, 0, 0, totalImages,
                Instant.now(), null, null, null));
        try {
            executor.execute(() -> runTask(datasetId, task));
            return true;
        } catch (RuntimeException e) {
            syncingDatasetIds.remove(datasetId);
            snapshots.computeIfPresent(datasetId, (id, current) -> new TaskSnapshot(
                    SyncStatus.FAILED, SyncStage.FAILED, current.progress(),
                    current.processedImages(), current.totalImages(), current.submittedAt(),
                    current.startedAt(), Instant.now(), errorMessage(e)));
            throw e;
        }
    }

    public boolean isSyncing(Long datasetId) {
        return syncingDatasetIds.contains(datasetId);
    }

    public String getLastError(Long datasetId) {
        TaskSnapshot snapshot = snapshots.get(datasetId);
        return snapshot == null ? null : snapshot.error();
    }

    public TaskSnapshot getSnapshot(Long datasetId) {
        return snapshots.get(datasetId);
    }

    public void updateProgress(Long datasetId, SyncStage stage, int progress, int processedImages) {
        snapshots.computeIfPresent(datasetId, (id, current) -> {
            if (current.status() != SyncStatus.RUNNING) {
                return current;
            }
            int boundedProgress = Math.max(current.progress(), Math.min(progress, 99));
            int boundedProcessed = Math.max(current.processedImages(), processedImages);
            return new TaskSnapshot(
                    current.status(), stage, boundedProgress, boundedProcessed,
                    current.totalImages(), current.submittedAt(), current.startedAt(),
                    current.finishedAt(), current.error());
        });
    }

    private void runTask(Long datasetId, Runnable task) {
        snapshots.computeIfPresent(datasetId, (id, current) -> new TaskSnapshot(
                SyncStatus.RUNNING, SyncStage.PREPARING, 1, current.processedImages(),
                current.totalImages(), current.submittedAt(), Instant.now(), null, null));
        try {
            task.run();
            snapshots.computeIfPresent(datasetId, (id, current) -> new TaskSnapshot(
                    SyncStatus.SUCCEEDED, SyncStage.COMPLETED, 100,
                    current.totalImages() == null ? current.processedImages() : current.totalImages(),
                    current.totalImages(), current.submittedAt(), current.startedAt(),
                    Instant.now(), null));
        } catch (Exception e) {
            snapshots.computeIfPresent(datasetId, (id, current) -> new TaskSnapshot(
                    SyncStatus.FAILED, SyncStage.FAILED, current.progress(),
                    current.processedImages(), current.totalImages(), current.submittedAt(),
                    current.startedAt(), Instant.now(), errorMessage(e)));
            logger.error("数据集 {} 同步到 MinIO 失败", datasetId, e);
        } finally {
            syncingDatasetIds.remove(datasetId);
        }
    }

    private static String errorMessage(Exception e) {
        return e.getMessage() == null || e.getMessage().isBlank()
                ? "同步失败，请查看服务日志"
                : e.getMessage();
    }

    public enum SyncStatus {
        QUEUED,
        RUNNING,
        SUCCEEDED,
        FAILED
    }

    public enum SyncStage {
        WAITING,
        PREPARING,
        EXPORTING,
        PACKAGING,
        UPLOADING,
        FINALIZING,
        COMPLETED,
        FAILED
    }

    public record TaskSnapshot(
            SyncStatus status,
            SyncStage stage,
            int progress,
            int processedImages,
            Integer totalImages,
            Instant submittedAt,
            Instant startedAt,
            Instant finishedAt,
            String error) {
    }
}
