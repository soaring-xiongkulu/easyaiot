package com.basiclab.iot.file.service;

import com.basiclab.iot.common.exception.BaseException;
import com.basiclab.iot.file.domain.vo.BucketVo;
import com.basiclab.iot.file.utils.FileUploadUtils;
import com.github.pagehelper.PageInfo;
import io.minio.ComposeSource;
import io.minio.errors.*;
import io.minio.messages.Bucket;
import io.minio.messages.DeleteObject;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 本地文件存储
 * 
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@RefreshScope
//@Primary
@Service
public class LocalSysFileServiceImpl implements ISysFileService
{
    /**
     * 资源映射路径 前缀
     */
    @Value("${file.prefix}")
    public String localFilePrefix;

    /**
     * 域名或本机访问地址
     */
    @Value("${file.domain}")
    public String domain;
    
    /**
     * 上传文件存储在本地的根路径
     */
    @Value("${file.path}")
    private String localFilePath;

    /**
     * 本地文件上传接口
     * 
     * @param file 上传的文件
     * @return 访问地址
     * @throws Exception
     */
    @Override
    public String uploadFile(MultipartFile file) throws Exception
    {
        String name = FileUploadUtils.upload(localFilePath, file);
        String url = domain + localFilePrefix + name;
        return url;
    }

    @Override
    public String uploadFile(MultipartFile file, String bucketName) throws Exception {
        return "";
    }

    /**
     * 删除文件
     *
     * @param bucketName
     * @param objectName
     */
    @Override
    public void removeFile(String bucketName, String objectName) {
    }

    @Override
    public Object getConfig() {
        return null;
    }

    @Override
    public boolean bucketExists(String bucketName) {
        return false;
    }

    @Override
    public boolean createBucket(String bucketName) {
        return false;
    }

    @Override
    public void removeBucket(String bucketName) throws Exception {

    }

    @Override
    public PageInfo<BucketVo> getAllBuckets(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize) {
        return null;
    }

    @Override
    public PageInfo<Map<String,Object>> getFileList(String bucketName, String prefix, String key, Integer pageNum, Integer pageSize) {
        return null;
    }

    @Override
    public boolean uploadFile(String fileName, String bucketName, InputStream stream, Long fileSize, String type) {
        return false;
    }

    @Override
    public boolean uploadChunkedFile(String filePath, String fileName, InputStream stream, String bucketName) {
        return false;
    }

    @Override
    public void upload(String filePrefix, String fileName, int chunksCount, int chunkSize, FileInputStream fis, ThreadPoolExecutor executor) throws IOException {

    }

    @Override
    public void merge(String filePrefix, String fileName, String bucketName, List<ComposeSource> sourceObjectList, List<DeleteObject> objects) throws ErrorResponseException, InsufficientDataException, InternalException, InvalidKeyException, InvalidResponseException, IOException, NoSuchAlgorithmException, BaseException {

    }

    @Override
    public boolean downloadChunkedFile(String filePath, String fileName, String bucketName) {
        return false;
    }

    @Override
    public void weiteToFile(InputStream inputStream, String filePath, long offset) {

    }

    @Override
    public boolean download(String bucketName, String objectName, String fileName) {
        return false;
    }

    @Override
    public InputStream getObject(String bucketName, String objectName) throws IOException, InvalidKeyException, InvalidResponseException, InsufficientDataException, NoSuchAlgorithmException, BaseException, InternalException, ErrorResponseException {
        return null;
    }

    @Override
    public Boolean folderExists(String bucketName, String prefix) throws Exception {
        return null;
    }

    @Override
    public void createFolder(String bucketName, String path) throws Exception {

    }

    @Override
    public String getUrl(String objectName, String bucketName) throws Exception {
        return "";
    }

    @Override
    public boolean delete(String bucketName, String fileName) {
        return false;
    }

    @Override
    public boolean deletes(String bucketName, List<DeleteObject> list) {
        return false;
    }

    @Override
    public boolean objectExists(String bucketName, String fileName) {
        return false;
    }
}
