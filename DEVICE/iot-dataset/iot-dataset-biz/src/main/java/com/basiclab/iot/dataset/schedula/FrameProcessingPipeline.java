package com.basiclab.iot.dataset.schedula;



import com.basiclab.iot.common.text.UUID;
import com.basiclab.iot.common.utils.DateUtils;
import com.basiclab.iot.dataset.cache.StreamUrlCache;
import com.basiclab.iot.dataset.dal.dataobject.DatasetImageDO;
import com.basiclab.iot.dataset.dal.pgsql.DatasetImageMapper;
import io.minio.MinioClient;
import io.minio.UploadObjectArgs;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.bytedeco.javacv.FFmpegFrameGrabber;
import org.bytedeco.javacv.Frame;
import org.bytedeco.javacv.Java2DFrameConverter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

import javax.annotation.PostConstruct;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.concurrent.*;

/**
 * FrameProcessingPipeline
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@EnableScheduling
@Configuration
public class FrameProcessingPipeline {
    private static final Logger log = LoggerFactory.getLogger(FrameProcessingPipeline.class);

    @Value("${minio.bucket}")
    private String minioBucket;

    @Autowired
    private MinioClient minioClient;

    // 环形队列
    private final BlockingQueue<FrameCaptureTask> captureQueue = new ArrayBlockingQueue<>(200);
    private final BlockingQueue<FrameCaptureTask> saveDatabaseQueue = new ArrayBlockingQueue<>(200);

    // 线程池
    private final ExecutorService capturePool = Executors.newCachedThreadPool();
    private final ExecutorService uploadPool = Executors.newFixedThreadPool(5);
    private final ExecutorService dbPool = Executors.newFixedThreadPool(3);

    // 依赖
    @Autowired
    private StreamUrlCache urlCache;
    @Autowired
    private DatasetImageMapper datasetImageMapper;

    @PostConstruct
    private void init() {
        new File("/tmp/frames").mkdirs();
        startUploadStage();
        startDatabaseStage();
    }

    // ========== 定时任务入口 ==========
    @Scheduled(fixedRate = 1000 * 60)
    public void scheduledCapture() {
        List<Map<String, String>> streams = urlCache.getCachedUrls();
        if (streams.isEmpty()) {
            return;
        }

        // 为每个URL提交抽帧任务
        streams.forEach(stream -> capturePool.submit(() -> {
            try {
                captureFrame(stream);
            } catch (Exception e) {
                // 错误处理
                log.error(e.getMessage(), e);
            }
        }));
    }

    // ========== 第一阶段：抽帧 ==========
    private void captureFrame(Map<String, String> streams) throws Exception {
        String datasetId = streams.get("datasetId");
        String rtmpUrl = streams.get("rtmpUrl");
        FFmpegFrameGrabber grabber = new FFmpegFrameGrabber(rtmpUrl);
        grabber.start();

        try {
            // 获取一帧图像
            Frame frame = grabber.grabImage();
            if (frame == null) return;

            // 生成唯一文件名
            String fileName = "frame_" + UUID.randomUUID() + ".jpg";
            File outputFile = new File("/tmp/frames", fileName);

            // 保存为JPEG
            Java2DFrameConverter converter = new Java2DFrameConverter();
            BufferedImage image = converter.convert(frame);
            ImageIO.write(image, "jpg", outputFile);

            // 获取图片宽高
            int width = image.getWidth();
            int height = image.getHeight();

            // 创建任务对象
            FrameCaptureTask task = new FrameCaptureTask(datasetId, rtmpUrl, fileName, outputFile, width, height, new Date());

            // 放入队列（阻塞式）
            captureQueue.put(task);
        } finally {
            grabber.stop();
        }
    }

    // ========== 第二阶段：上传Minio ==========
    private void startUploadStage() {
        for (int i = 0; i < 5; i++) {
            uploadPool.submit(() -> {
                List<FrameCaptureTask> batch = new ArrayList<>(50);
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        // 批量收集任务
                        FrameCaptureTask task = captureQueue.poll(100, TimeUnit.MILLISECONDS);
                        if (task != null) {
                            batch.add(task);
                        }

                        // 批量处理
                        if (batch.size() >= 50 || (!batch.isEmpty() && task == null)) {
                            batchUploadToMinio(batch);
                            batch.clear();
                        }
                    } catch (Exception e) {
                        // 错误处理
                        log.error(e.getMessage(), e);
                    }
                }
            });
        }
    }

    private void batchUploadToMinio(List<FrameCaptureTask> tasks) {
        // 并行上传
        tasks.parallelStream().forEach(task -> {
            try {
                minioClient.uploadObject(
                        UploadObjectArgs.builder()
                                .bucket(minioBucket)
                                .object(task.getDatasetId() + "/" + task.getFileName())
                                .filename(task.getFile().getAbsolutePath())
                                .build());

                // 放入下一阶段
                saveDatabaseQueue.put(task);

                // 删除临时文件
                task.getFile().delete();
            } catch (Exception e) {
                // 错误处理
                log.error(e.getMessage(), e);
            }
        });
    }

    // ========== 第三阶段：存储数据库 ==========
    private void startDatabaseStage() {
        for (int i = 0; i < 3; i++) {
            dbPool.submit(() -> {
                List<DatasetImageDO> batch = new ArrayList<>(50);
                while (!Thread.currentThread().isInterrupted()) {
                    try {
                        // 批量收集任务
                        FrameCaptureTask task = saveDatabaseQueue.poll(100, TimeUnit.MILLISECONDS);
                        if (task != null) {
                            //http://14.18.122.2:9001/api/v1/buckets/alarm/objects/download?prefix=live/stream1/25031415040675396904.jpg&version_id=null
                            DatasetImageDO datasetImageDO = new DatasetImageDO();
                            datasetImageDO.setDatasetId(Long.valueOf(task.getDatasetId()));
                            datasetImageDO.setName(task.getFileName());
                            datasetImageDO.setWidth(task.getWidth());
                            datasetImageDO.setHeigh(task.getHeigh());
                            datasetImageDO.setSize(task.getFile().length());
                            datasetImageDO.setCreateTime(DateUtils.dateToLocalDateTime(task.getCaptureTime()));
                            datasetImageDO.setUpdateTime(DateUtils.dateToLocalDateTime(task.getCaptureTime()));
                            datasetImageDO.setPath("/api/v1/buckets/" + minioBucket + "/objects/download?prefix=" + task.getDatasetId() + "/" + task.getFileName());
                            batch.add(datasetImageDO);
                        }

                        // 批量保存
                        if (batch.size() >= 50 || (!batch.isEmpty() && task == null)) {
                            datasetImageMapper.insertBatch(batch);
                            batch.clear();
                        }
                    } catch (Exception e) {
                        // 错误处理
                        log.error(e.getMessage(), e);
                    }
                }
            });
        }
    }

    // ========== 任务对象 ==========
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    private static class FrameCaptureTask {
        private String datasetId;
        private String rtmpUrl;
        private String fileName;
        private File file;
        private int width;
        private int heigh;
        private Date captureTime;
    }
}
