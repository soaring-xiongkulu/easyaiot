package com.basiclab.iot.file.service;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;

import com.basiclab.iot.common.exception.BaseException;
import com.basiclab.iot.file.config.MinioConfig;
import com.basiclab.iot.file.domain.vo.BucketVo;
import com.github.pagehelper.Page;
import com.github.pagehelper.PageInfo;
import io.minio.*;
import io.minio.errors.*;
import io.minio.http.Method;
import io.minio.messages.Bucket;
import io.minio.messages.DeleteError;
import io.minio.messages.DeleteObject;
import io.minio.messages.Item;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Minio 文件存储
 *
 * @author EasyAIoT
 */
@RefreshScope
@Primary
@Service
@Slf4j
public class MinioSysFileServiceImpl implements ISysFileService {
    @Autowired
    private MinioConfig minioConfig;

    @Autowired
    private MinioClient minioClient;

    /**
     * #5M 单位围为M
     */
    @Value("${minio.chunk}")
    private int chunk;

    /**
     * #分块合并大小
     */
    @Value("${minio.chunkSize}")
    private int chunkSize;

    /**
     * 默认超时时间
     */
    private static final int DEFAULT_EXPIRY_TIME = 7 * 24 * 3600;
    private static final Object lock = new Object();

    @Override
    public Object getConfig() {
        return minioConfig;
    }

    /**
     * 本地文件上传接口
     *
     * @param file 上传的文件
     * @return 访问地址
     * @throws Exception
     */
    @Override
    public String uploadFile(MultipartFile file) throws Exception {
//        String fileName = FileUploadUtils.extractFilename(file);
        String fileName = file.getOriginalFilename();
        PutObjectArgs args = PutObjectArgs.builder()
                .bucket(minioConfig.getBucketName())
                .object(fileName)
                .stream(file.getInputStream(), file.getSize(), -1)
                .contentType(file.getContentType())
                .build();
        minioClient.putObject(args);
        return minioConfig.getDownloadUrl() + "/api/v1/buckets/" + minioConfig.getBucketName() + "/objects/download?prefix=" + fileName;
    }

    /**
     * 本地文件上传接口（根据桶名称）
     *
     * @param file 上传的文件
     * @return 访问地址
     * @throws Exception
     */
    @Override
    public String uploadFile(MultipartFile file, String bucketName) throws Exception {
        String fileName = file.getOriginalFilename();
        PutObjectArgs args = PutObjectArgs.builder()
                .bucket(bucketName)
                .object(fileName)
                .stream(file.getInputStream(), file.getSize(), -1)
                .contentType(file.getContentType())
                .build();
        minioClient.putObject(args);
        return minioConfig.getDownloadUrl() + "/api/v1/buckets/" + minioConfig.getBucketName() + "/objects/download?prefix=" + fileName;
    }

    /**
     * 删除文件
     *
     * @param bucketName
     * @param objectName
     */
    @Override
    public void removeFile(String bucketName, String objectName) {

        RemoveObjectArgs removeObjectArgs = RemoveObjectArgs.builder()
                .bucket(bucketName)
                .object(objectName).build();
        try {
            minioClient.removeObject(removeObjectArgs);
        } catch (Exception e) {
            log.error("删除minio文件异常", e);
        }
    }

    /**
     * 判断bucket是否存在
     *
     * @return
     */
    public boolean bucketExists(String bucketName) {
        boolean exists = false;
        try {
            if (StringUtils.isNotBlank(bucketName))
                exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucketName).build());
        } catch (Exception e) {
            log.error("判断bucket是否存在 异常e", e.getMessage());
            e.printStackTrace();
        }
        return exists;
    }

    /**
     * 创建桶
     */
    public boolean createBucket(String bucketName) {
        try {
            if (!bucketExists(bucketName)) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
                return true;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
        return false;
    }


    /**
     * 删除桶
     */
    public void removeBucket(String bucketName) throws Exception {
        if (bucketExists(bucketName))
            minioClient.removeBucket(RemoveBucketArgs.builder().bucket(bucketName).build());
    }

    @Override
    public PageInfo<BucketVo> getAllBuckets(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize) {
        List<BucketVo> reslut = new ArrayList<>();
            List<Bucket> buckets = null;
            try {
                buckets = minioClient.listBuckets();
            } catch (InvalidKeyException | ErrorResponseException | InsufficientDataException | InternalException
                    | InvalidResponseException | NoSuchAlgorithmException | ServerException | XmlParserException
                    | IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
            for (Bucket bucket : buckets) {
                //按照文件名称过滤
                if (!(StrUtil.isBlank(key) || ObjectUtil.equals(bucket.name(), key))) {
                    continue;
                }
                BucketVo bucketVo = new BucketVo();
                bucketVo.setName(bucket.name());
                bucketVo.setCreationDate(bucket.creationDate());
                reslut.add(bucketVo);
            }
        //桶列表分页
        return startPage(reslut, pageNum, pageSize);
    }

    /**
     * 获取minio中,某个bucket中所有的文件名
     */
    @SneakyThrows
    public PageInfo<Map<String, Object>> getFileList(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize) {
        List<Map<String, Object>> reslut = new ArrayList<>();
        if (bucketExists(bucketName)) {
            Iterable<Result<Item>> items = minioClient.listObjects(ListObjectsArgs.builder().bucket(bucketName).prefix(prefix)
                    .recursive(true).build());
            List<Item> items1 = new ArrayList<>();
            Iterator iterator = items.iterator();
            while (iterator.hasNext()) {
                Result<Item> itemResult = (Result<Item>) iterator.next();
                Item item = itemResult.get();
                items1.add(item);
            }
            //按最后修改时间排序
            items1.sort((item1, item2) -> item2.lastModified().compareTo(item1.lastModified()));
            for (Item i : items1) {
                //按照文件名称过滤
                if (!(StrUtil.isBlank(key) || ObjectUtil.equals(i.objectName(), key))) {
                    continue;
                }
                Map<String, Object> resultMap = new HashMap<>();
//                String url = getUrl(bucketName, i.objectName());
                String url = minioConfig.getDownloadUrl() + "/api/v1/buckets/" + minioConfig.getBucketName() + "/objects/download?prefix=" + i.objectName();
                resultMap.put("objectName", i.objectName());
                resultMap.put("url", url);
                resultMap.put("lastModified", i.lastModified());
                resultMap.put("size", i.size());
                resultMap.put("isDir", i.isDir());
                reslut.add(resultMap);
            }
        }
        //文件列表分页
        return startPage(reslut, pageNum, pageSize);
    }

    public static <T> PageInfo<T> startPage(List<T> list, Integer pageNum, Integer pageSize) {
        //创建Page类
        Page<T> page = new Page<>(pageNum, pageSize);
        //为Page类中的total属性赋值
        page.setTotal(list.size());
        //计算当前需要显示的数据下标起始值
        int startIndex = (pageNum - 1) * pageSize;
        int endIndex = Math.min(startIndex + pageSize, list.size());
        //从链表中截取需要显示的子链表，并加入到Page
        page.addAll(list.subList(startIndex, endIndex));
        //以Page创建PageInfo
        return new PageInfo<>(page);
    }


    /**
     * 上传
     */
    public boolean uploadFile(String fileName, String bucketName, InputStream stream, Long fileSize, String type) {
        try {
            minioClient.putObject(PutObjectArgs.builder().bucket(bucketName).object(fileName).stream(stream, fileSize, -1)
                    .contentType(type).build());
            return true;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return false;
    }

    /**
     * 分块上传
     *
     * @return
     */
    public boolean uploadChunkedFile(String filePath, String fileName, InputStream stream, String bucketName) {
        try {
            //作临时桶
            String filePrefix = fileName.substring(0, fileName.lastIndexOf("."));
            if (!bucketExists(filePrefix))
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(filePrefix).build());
            if (!bucketExists(bucketName))
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());

            //创建后续需要分块的集合
            List<ComposeSource> sourceObjectList = new ArrayList<ComposeSource>();

            FileInputStream fis = new FileInputStream(filePath);
            long fileSize = fis.getChannel().size();
            int chunksCount = (int) Math.ceil((double) fileSize / (chunk * 1024 * 1024));

            ThreadPoolExecutor executor = new ThreadPoolExecutor(
                    10, // 核心线程数
                    20, // 最大线程数
                    60L, // 线程空闲超时时间（单位：秒）
                    TimeUnit.SECONDS, // 线程空闲超时时间单位
                    new ArrayBlockingQueue<>(chunksCount), // 任务队列大小
                    Executors.defaultThreadFactory(), // 线程工厂
                    new ThreadPoolExecutor.AbortPolicy() // 拒绝策略
            );

            upload(filePrefix, fileName, chunksCount, (int) chunk * 1024 * 1024, fis, executor);
            List<DeleteObject> objects = new LinkedList<DeleteObject>();
            for (int i = 0; i < chunksCount; i++) {
                objects.add(new DeleteObject(fileName + i));
                sourceObjectList.add(ComposeSource.builder().bucket(filePrefix).object(fileName + i).build());
            }

            merge(filePrefix, fileName, bucketName, sourceObjectList, objects);

            //删除最后一次合并的文件
            deletes(filePrefix, objects);
            //删除临时桶
            removeBucket(filePrefix);
            return true;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    /**
     * 分块上传
     *
     * @param fileName
     * @param filePrefix
     * @param chunksCount
     * @param chunkSize
     * @param fis
     * @param executor
     * @throws IOException
     */
    public void upload(String filePrefix, String fileName, int chunksCount, int chunkSize, FileInputStream fis, ThreadPoolExecutor executor) throws IOException {
        log.info("开始准备上传---------------------------------------------");
        // 依次上传每个分块。
        for (int i = 0; i < chunksCount; i++) {
            int index = i;
            byte[] buffer = new byte[chunkSize];
            int bytesRead = fis.read(buffer);

            if (bytesRead == -1) {
                break;
            }
            executor.execute(new Runnable() {
                @Override
                public void run() {
                    // 上传每个分块。
                    try {
                        //log.info("--------------------------------------");
                        ByteArrayInputStream byteArrayInputStream = new ByteArrayInputStream(buffer);
                        minioClient.putObject(
                                PutObjectArgs.builder()
                                        .bucket(filePrefix)
                                        .object(fileName + index)
                                        .stream(byteArrayInputStream, bytesRead, -1)
                                        .build());
                        byteArrayInputStream.close();
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                }
            });
        }
        // 等待所有的分片完成
        // shutdown方法：通知各个任务（Runnable）的运行结束
        executor.shutdown();
        while (!executor.isTerminated()) {
            try {
                // 指定的时间内所有的任务都结束的时候，返回true，反之返回false，返回false还有执行完的任务
                executor.awaitTermination(3, TimeUnit.SECONDS);
            } catch (InterruptedException e) {
                log.error(e.getMessage());
            }
        }
        fis.close();
        log.info("上传完成---------------------------------------------");
    }

    /**
     * 合并
     *
     * @param fileName
     * @param bucketName
     * @param filePrefix       临时桶
     * @param sourceObjectList
     * @throws ErrorResponseException
     * @throws InsufficientDataException
     * @throws InternalException
     * @throws InvalidKeyException
     * @throws InvalidResponseException
     * @throws IOException
     * @throws NoSuchAlgorithmException
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    public void merge(String filePrefix, String fileName, String bucketName, List<ComposeSource> sourceObjectList, List<DeleteObject> objects)
            throws ErrorResponseException, InsufficientDataException, InternalException, InvalidKeyException, InvalidResponseException, IOException, NoSuchAlgorithmException, ServerException, XmlParserException, IllegalArgumentException {
        ThreadPoolExecutor executor;
        int sourceSize = (int) Math.ceil((double) sourceObjectList.size() / chunkSize);
        if (sourceSize > 1) {
            executor = new ThreadPoolExecutor(
                    10, // 核心线程数
                    20, // 最大线程数
                    60L, // 线程空闲超时时间（单位：秒）
                    TimeUnit.SECONDS, // 线程空闲超时时间单位
                    new ArrayBlockingQueue<>(sourceSize), // 任务队列大小
                    Executors.defaultThreadFactory(), // 线程工厂
                    new ThreadPoolExecutor.AbortPolicy() // 拒绝策略
            );

            for (int i = 0; i < sourceSize; i++) {
                int index = i;
                int start = i * chunkSize;
                int end = Math.min(start + chunkSize, sourceObjectList.size());
                log.info("start: {}, ebd: {}", start, end);
                List<ComposeSource> composeSources = sourceObjectList.subList(start, end);
                executor.submit(() -> {

                    // 调用composeObject方法合并分片
                    try {
                        List<ComposeSource> subSources = composeSources;
                        minioClient.composeObject(ComposeObjectArgs.builder()
                                .bucket(filePrefix)
                                .object(fileName + "-" + index)
                                .sources(subSources)
                                .build());
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                });
            }
            // 等待所有的分片完成
            // shutdown方法：通知各个任务（Runnable）的运行结束
            executor.shutdown();
            while (!executor.isTerminated()) {
                try {
                    // 指定的时间内所有的任务都结束的时候，返回true，反之返回false，返回false还有执行完的任务
                    executor.awaitTermination(3, TimeUnit.SECONDS);
                } catch (InterruptedException e) {
                    log.error(e.getMessage());
                }
            }

            sourceObjectList = new ArrayList<>();
            for (int i = 0; i < sourceSize; i++) {
                sourceObjectList.add(ComposeSource.builder().bucket(filePrefix).object(fileName + "-" + i).build());
                objects.add(new DeleteObject(fileName + "-" + i));
            }
        }

        minioClient.composeObject(ComposeObjectArgs.builder()
                .bucket(bucketName)
                .object(fileName)
                .sources(sourceObjectList)
                .build());
        log.info("合并完成---------------------------------------------");
    }

    /**
     * 分块下载
     */
    public boolean downloadChunkedFile(String filePath, String fileName, String bucketName) {
        if (!bucketExists(bucketName)) return false;

        try {
            StatObjectResponse statObjectResponse = minioClient.statObject(StatObjectArgs.builder().bucket(bucketName).object(fileName).build());

            int totalParts = (int) Math.ceil((double) statObjectResponse.size() / (chunk * 1024 * 1024));

            ThreadPoolExecutor executor = new ThreadPoolExecutor(
                    10, // 核心线程数
                    20, // 最大线程数
                    60L, // 线程空闲超时时间（单位：秒）
                    TimeUnit.SECONDS, // 线程空闲超时时间单位
                    new ArrayBlockingQueue<>(totalParts + 1), // 任务队列大小
                    Executors.defaultThreadFactory(), // 线程工厂
                    new ThreadPoolExecutor.AbortPolicy() // 拒绝策略
            );

            for (int i = 0; i < totalParts; i++) {
                long offset = i;
                executor.execute(new Runnable() {
                    @Override
                    public void run() {
                        synchronized (statObjectResponse) {
                            InputStream inputStream = null;
                            long index = offset;
                            long length = chunk * 1024 * 1024;
                            index = index * length;
                            if (index + length > statObjectResponse.size()) {
                                length = statObjectResponse.size() - index;
                                log.info("最后一次：offset:{} , index:{},  let: {} , cout:{} ", offset, index, length, statObjectResponse.size());
                            }
                            log.info("offset:{} , index:{},  let: {} , cout:{} ", offset, index, length, statObjectResponse.size());
                            // 下载
                            try {
                                inputStream = minioClient.getObject(GetObjectArgs
                                        .builder()
                                        .bucket(bucketName)
                                        .object(fileName)
                                        .length(length)
                                        .offset(index)
                                        .build());

                                weiteToFile(inputStream, filePath, index);

                            } catch (Exception e) {
                                throw new RuntimeException(e);
                            } finally {
                                if (null != inputStream) {
                                    try {
                                        inputStream.close();
                                    } catch (IOException e) {
                                        throw new RuntimeException(e);
                                    }
                                }
                            }
                        }
                    }
                });
            }
            executor.shutdown();
            while (!executor.isTerminated()) {
                try {
                    // 指定的时间内所有的任务都结束的时候，返回true，反之返回false，返回false还有执行完的任务
                    executor.awaitTermination(3, TimeUnit.SECONDS);
                } catch (InterruptedException e) {
                    log.error(e.getMessage());
                }
            }
            return true;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }

    }

    /**
     * 保存到文件
     *
     * @param inputStream
     * @param filePath
     * @param offset
     */
    public void weiteToFile(InputStream inputStream, String filePath, long offset) {
        byte[] buffer = new byte[1024];
        int bytesRead;
        try (RandomAccessFile file = new RandomAccessFile(filePath, "rw")) {
            synchronized (lock) {
                file.seek(offset);
                while ((bytesRead = inputStream.read(buffer)) != -1) {
                    file.write(buffer, 0, bytesRead);
                }
                file.getFD().sync();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 直接下载
     *
     * @param bucketName
     * @param objectName
     * @param fileName
     * @return
     * @throws Exception
     */
    public boolean download(String bucketName, String objectName, String fileName) {

        try {
            minioClient.downloadObject(DownloadObjectArgs
                    .builder()
                    .bucket(bucketName)
                    .object(objectName)
                    .filename(fileName)
                    .build());
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        return false;
    }

    /**
     * 获取文件流
     *
     * @param bucketName bucket名称
     * @param objectName 文件名称
     * @return 二进制流
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    public InputStream getObject(String bucketName, String objectName)
            throws IOException, InvalidKeyException, InvalidResponseException, InsufficientDataException, NoSuchAlgorithmException, BaseException, InternalException, ErrorResponseException, ServerException, XmlParserException, IllegalArgumentException {
        return minioClient.getObject(GetObjectArgs.builder().bucket(bucketName).object(objectName).build());
    }


    /**
     * 判断文件夹是否存在
     *
     * @return
     */
    public Boolean folderExists(String bucketName, String prefix) throws Exception {
        Iterable<Result<Item>> results = minioClient.listObjects(ListObjectsArgs.builder().bucket(bucketName).prefix(
                prefix).recursive(false).build());
        for (Result<Item> result : results) {
            Item item = result.get();
            if (item.isDir()) {
                return true;
            }
        }
        return false;
    }

    /**
     * 创建文件夹
     *
     * @param bucketName 桶名称
     * @param path       路径
     */
    public void createFolder(String bucketName, String path) throws Exception {
        minioClient.putObject(PutObjectArgs.builder().bucket(bucketName).object(path)
                .stream(new ByteArrayInputStream(new byte[]{}), 0, -1).build());
    }

    /**
     * 获取文件在minio在服务器上的外链
     */
    public String getUrl(String bucketName, String objectName) throws Exception {
        Object config = getConfig();
        MinioConfig minioConfig = (MinioConfig) config;
        MinioClient minioClient = MinioClient.builder().endpoint("iot.basiclab.top").credentials(minioConfig.getAccessKey(), minioConfig.getSecretKey()).build();
        return minioClient.getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder().method(Method.GET).bucket(
                bucketName).object(objectName).expiry(1, TimeUnit.DAYS).build());
    }

    /**
     * 删除文件
     *
     * @param bucketName
     * @param fileName
     */
    public boolean delete(String bucketName, String fileName) {
        if (bucketExists(bucketName)) {
            if (objectExists(bucketName, fileName)) {
                try {
                    minioClient.removeObject(
                            RemoveObjectArgs.builder().bucket(bucketName).object(fileName).build());
                    return true;
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }
        }
        return false;
    }

    /**
     * 批量删除文件
     *
     * @param bucketName
     * @param list
     */
    public boolean deletes(String bucketName, List<DeleteObject> list) {
        if (bucketExists(bucketName)) {
            try {
                Iterable<Result<DeleteError>> results =
                        minioClient.removeObjects(
                                RemoveObjectsArgs.builder().bucket(bucketName).objects(list).build());
                for (Result<DeleteError> result : results) {
                    DeleteError error = result.get();
                    System.out.println(
                            "Error in deleting object " + error.objectName() + "; " + error.message());
                }
                return true;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
        return false;
    }

    /**
     * 判断文件是否存在
     *
     * @param bucketName
     * @param fileName
     */
    public boolean objectExists(String bucketName, String fileName) {
        if (bucketExists(bucketName)) {
            try {
                minioClient.statObject(
                        StatObjectArgs.builder().bucket(bucketName).object(fileName).build());
                return true;
            } catch (Exception e) {
                if (e.getMessage().equals("Object does not exist")) {
                    return false;
                }
            }
        }
        return false;
    }
}
