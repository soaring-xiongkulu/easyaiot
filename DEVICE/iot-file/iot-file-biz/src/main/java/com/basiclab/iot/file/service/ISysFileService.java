package com.basiclab.iot.file.service;

import com.basiclab.iot.common.exception.BaseException;
import com.basiclab.iot.file.domain.vo.BucketVo;
import com.github.pagehelper.PageInfo;
import io.minio.ComposeSource;
import io.minio.errors.*;
import io.minio.messages.Bucket;
import io.minio.messages.DeleteObject;
import org.springframework.web.multipart.MultipartFile;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 文件上传接口
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
public interface ISysFileService {
    /**
     * 文件上传接口
     *
     * @param file
     * @return
     * @throws Exception
     */
    String uploadFile(MultipartFile file) throws Exception;

    /**
     * 文件上传接口（根据桶名称）
     * @param file
     * @param bucketName
     * @return
     * @throws Exception
     */
    String uploadFile(MultipartFile file, String bucketName) throws Exception;

    /**
     * 删除文件
     *
     * @param bucketName
     * @param objectName
     */
    void removeFile(String bucketName, String objectName);

    /**
     * 获取配置信息
     *
     * @return
     */
    Object getConfig();

    /**
     * 判断bucket是否存在
     *
     * @return
     */
    boolean bucketExists(String bucketName);

    /**
     * 创建桶
     */
    boolean createBucket(String bucketName);

    /**
     * 删除桶
     */
    void removeBucket(String bucketName) throws Exception;

    /**
     * 获取minio中,所有bucket信息
     */
    PageInfo<BucketVo> getAllBuckets(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize) throws InsufficientDataException, ErrorResponseException, IOException, NoSuchAlgorithmException, InvalidKeyException, InvalidResponseException, InternalException;

    /**
     * 获取minio中,某个bucket中所有的文件名
     */
    PageInfo<Map<String,Object>> getFileList(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize);

    /**
     * 上传
     */
    boolean uploadFile(String fileName, String bucketName, InputStream stream, Long fileSize, String type);

    /**
     * 分块上传
     *
     * @return
     */
    boolean uploadChunkedFile(String filePath, String fileName, InputStream stream, String bucketName);

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
    void upload(String filePrefix, String fileName, int chunksCount, int chunkSize, FileInputStream fis, ThreadPoolExecutor executor) throws IOException;

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
     * @throws BaseException
 * @throws IllegalArgumentException 
 * @throws ServerException 
     * @throws XmlParserException
     */
    void merge(String filePrefix, String fileName, String bucketName, List<ComposeSource> sourceObjectList, List<DeleteObject> objects)
            throws ErrorResponseException, InsufficientDataException, InternalException, InvalidKeyException, InvalidResponseException, IOException, NoSuchAlgorithmException, BaseException, ServerException, XmlParserException, IllegalArgumentException;

    /**
     * 分块下载
     */
    boolean downloadChunkedFile(String filePath, String fileName, String bucketName);

    /**
     * 保存到文件
     *
     * @param inputStream
     * @param filePath
     * @param offset
     */
    void weiteToFile(InputStream inputStream, String filePath, long offset);

    /**
     * 直接下载
     *
     * @param bucketName
     * @param objectName
     * @param fileName
     * @return
     * @throws Exception
     */
    boolean download(String bucketName, String objectName, String fileName);

    /**
     * 获取文件流
     *
     * @param bucketName bucket名称
     * @param objectName 文件名称
     * @return 二进制流
     * @throws BaseException 
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    InputStream getObject(String bucketName, String objectName)
            throws IOException, InvalidKeyException, InvalidResponseException, InsufficientDataException, NoSuchAlgorithmException, BaseException, InternalException, ErrorResponseException, BaseException, ServerException, XmlParserException, IllegalArgumentException;

    /**
     * 判断文件夹是否存在
     *
     * @return
     */
    Boolean folderExists(String bucketName, String prefix) throws Exception;

    /**
     * 创建文件夹
     *
     * @param bucketName 桶名称
     * @param path       路径
     */
    void createFolder(String bucketName, String path) throws Exception;

    /**
     * 获取文件在minio在服务器上的外链
     */
    String getUrl(String objectName, String bucketName) throws Exception;

    /**
     * 删除文件
     *
     * @param bucketName
     * @param fileName
     */
    boolean delete(String bucketName, String fileName);

    /**
     * 批量删除文件
     *
     * @param bucketName
     * @param list
     */
    boolean deletes(String bucketName, List<DeleteObject> list);

    /**
     * 判断文件是否存在
     *
     * @param bucketName
     * @param fileName
     */
    boolean objectExists(String bucketName, String fileName);
}
