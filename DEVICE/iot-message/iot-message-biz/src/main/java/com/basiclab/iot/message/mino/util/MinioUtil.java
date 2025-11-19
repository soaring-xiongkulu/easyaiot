package com.basiclab.iot.message.mino.util;

import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.core.util.ObjectUtil;
import com.alibaba.fastjson.JSON;
import com.baomidou.mybatisplus.core.toolkit.StringUtils;
import com.basiclab.iot.common.exception.BaseException;
import com.basiclab.iot.message.mino.config.MinioConfig;
import com.basiclab.iot.message.mino.vo.FileResVo;
import io.minio.*;
import io.minio.errors.*;
import io.minio.http.Method;
import io.minio.messages.Bucket;
import io.minio.messages.Item;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.PostConstruct;
import javax.servlet.http.HttpServletResponse;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * (minio工具类)
 *
 * @author zengzhaoyang
 * @date 2025/12/12
 */
@Component
@Slf4j
public class MinioUtil {

    @Autowired
    private MinioConfig minioConfig;

    private MinioClient minioClient;

    // 分享文件过期时间
    private static final int DEFAULT_EXPIRY_TIME = 7 * 24 * 3600;

    @PostConstruct
    private MinioClient client() {
        try {
            log.info("minioClient create start");
            minioClient = MinioClient
                    .builder()
                    .endpoint(minioConfig.getEndpoint() + ":" + minioConfig.getPort())
                    .credentials(minioConfig.getAccessKey(), minioConfig.getSecretKey())
                    .build();
            log.info("minioClient create end");
            // 创建常规桶，断点续传文件桶
            createBucket();
        } catch (Exception e) {
            log.error("连接MinIO服务器异常", e);
        }
        return minioClient;
    }

    /**
     * createBucket
     *
     * @param bucketName 桶名
     * @return void
     * @author zzy
     * @date 2025/12/12
     * @Param
     **/
    public void createBucket(String bucketName) {
        try {
            if (!client().bucketExists(BucketExistsArgs.builder().bucket(bucketName).build())) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucketName).build());
            }
        } catch (Exception e) {
            log.error("创建桶失败:{}", e);
        }
    }

    /**
     * 初始化Bucket
     * @throws IllegalArgumentException 
     * @throws ServerException 
     *
     * @throws Exception 异常
     */
    private void createBucket() throws
            BaseException,
            InsufficientDataException,
            ErrorResponseException,
            IOException,
            NoSuchAlgorithmException,
            InvalidKeyException,
            InvalidResponseException,
            XmlParserException,
            InternalException, ServerException, IllegalArgumentException {
        // 常规文件桶
        if (!minioClient.bucketExists(BucketExistsArgs.builder().bucket(minioConfig.getBucketName()).build())) {
            minioClient.makeBucket(MakeBucketArgs.builder().bucket(minioConfig.getBucketName()).build());
        }
        // 断点续传文件桶
        if (!minioClient.bucketExists(BucketExistsArgs.builder().bucket(minioConfig.getFileBreakPointBucketName()).build())) {
            minioClient.makeBucket(MakeBucketArgs.builder().bucket(minioConfig.getFileBreakPointBucketName()).build());
        }
    }

    /**
     * 判断文件是否存在
     *
     * @param bucketName 存储桶
     * @param objectName 文件夹+文件名
     * @return true：存在
     */
    public boolean doesObjectExist(String bucketName, String objectName) {
        boolean exist = true;
        try {
            minioClient.statObject(StatObjectArgs.builder().bucket(bucketName).object(objectName).build());
        } catch (Exception e) {
            exist = false;
        }
        return exist;
    }

    /**
     * 判断文件夹是否存在
     *
     * @param bucketName 存储桶
     * @param objectName 文件夹名称（去掉/）
     * @return true：存在
     */
    public boolean doesFolderExist(String bucketName, String objectName) {
        boolean exist = false;
        try {
            Iterable<Result<Item>> results = minioClient.listObjects(
                    ListObjectsArgs.builder().bucket(bucketName).prefix(objectName).recursive(false).build());
            for (Result<Item> result : results) {
                Item item = result.get();
                if (item.isDir() && objectName.equals(item.objectName())) {
                    exist = true;
                }
            }
        } catch (Exception e) {
            exist = false;
        }
        return exist;
    }

    /**
     * 通过MultipartFile，上传文件
     *
     * @param bucketName  存储桶
     * @param file        文件
     * @param objectName  对象名
     * @param contentType 文件类别
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    public ObjectWriteResponse putObject(String bucketName, MultipartFile file,
                                         String objectName, String contentType) throws IOException, BaseException, InsufficientDataException, ErrorResponseException, NoSuchAlgorithmException, InvalidKeyException, InvalidResponseException, InternalException, ServerException, XmlParserException, IllegalArgumentException {
        InputStream inputStream = file.getInputStream();
        return minioClient.putObject(
                PutObjectArgs.builder().bucket(bucketName).object(objectName).contentType(contentType)
                        .stream(inputStream, inputStream.available(), -1)
                        .build());
    }

    /**
     * 上传本地文件
     *
     * @param bucketName 存储桶
     * @param objectName 对象名称
     * @param fileName   本地文件路径
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    public ObjectWriteResponse putObject(String bucketName, String objectName,
                                         String fileName) throws IOException, BaseException, InsufficientDataException, ErrorResponseException, NoSuchAlgorithmException, InvalidKeyException, InvalidResponseException, InternalException, ServerException, XmlParserException, IllegalArgumentException {
        return minioClient.uploadObject(
                UploadObjectArgs.builder().bucket(bucketName).object(objectName).filename(fileName).build());
    }

    /**
     * 通过流上传文件
     *
     * @param bucketName  存储桶
     * @param objectName  文件对象
     * @param inputStream 文件流
     */
    public ObjectWriteResponse putObjectByStream(String bucketName, String objectName,
                                                 InputStream inputStream) {
        ObjectWriteResponse objectWriteResponse = null;
        try {
            objectWriteResponse = minioClient.putObject(
                    PutObjectArgs.builder().bucket(bucketName).object(objectName).stream(
                                    inputStream, inputStream.available(), -1)
                            .build());
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (inputStream != null) {
                try {
                    inputStream.close();
                } catch (IOException e) {
                    log.error("inputStream close IOException:" + e.getMessage());
                }
            }
        }
        return objectWriteResponse;
    }

    /**
     * 创建文件夹或目录
     *
     * @param bucketName 存储桶
     * @param objectName 目录路径
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     */
    public ObjectWriteResponse putDirObject(String bucketName, String objectName)
            throws BaseException, InsufficientDataException, ErrorResponseException, IOException, NoSuchAlgorithmException, InvalidKeyException, InvalidResponseException, InternalException, ServerException, XmlParserException, IllegalArgumentException {
        return minioClient.putObject(
                PutObjectArgs.builder().bucket(bucketName).object(objectName).stream(
                                new ByteArrayInputStream(new byte[]{}), 0, -1)
                        .build());
    }

    /**
     * @Title: uploadFile
     * @Description: (获取上传文件信息上传文件)
     * @author zzy
     * [file 上传文件（MultipartFile）, bucketName 桶名 , fileName 自定义文件名 ,fileFolderName 自定义文件夹名称]
     */
    public FileResVo uploadFile(MultipartFile file, String bucketName, String fileName, String fileFolderName)
            throws Exception {
        FileResVo res = new FileResVo();
        res.setCode(0);
        //判断文件是否为空
        if (null == file || 0 == file.getSize()) {
            res.setMsg("上传文件不能为空");
            return res;
        }
        if (StringUtils.isEmpty(bucketName)) {
            bucketName = minioConfig.getBucketName();
        }
        //判断存储桶是否存在  不存在则创建
        createBucket(bucketName);

        // 若未指定文件名称，则选择创建一个新的文件名称
        if (StringUtils.isEmpty(fileName)) {
            // 原始文件名
            String originalFilename = file.getOriginalFilename();
            // 拼接新的文件名
            fileName = UUID.randomUUID() + originalFilename.substring(originalFilename.lastIndexOf("."));
        }
        // 若未指定文件夹，则选择使用文件夹名称为
        if (StringUtils.isEmpty(fileFolderName)) {
            fileFolderName = new SimpleDateFormat("yyyy/MM/dd").format(new Date());
        }

        // 上传路径 = 文件夹 + 文件名
        String objectName = fileFolderName + fileName;

        //开始上传
        putObjectByStream(bucketName, objectName, file.getInputStream());

        res.setCode(1);
        res.setFileName(fileName);
        String url = minioConfig.getEndpoint() + ":" +
                minioConfig.getPort() + "/" +
                bucketName + "/" +
                objectName;
        res.setMsg(url);
        return res;
    }

    /**
     * 文件下载
     *
     * @param fileName   文件名
     * @param bucketName 桶名，若没有传输，则为默认桶
     * @param response   响应
     * @return void
     * @author zzy
     * @date 2025/12/13
     * @Param
     **/
    public void downloadFile(String fileName, String bucketName, HttpServletResponse response) {
        InputStream in = null;
        OutputStream out = null;

        if (StringUtils.isEmpty(bucketName)) {
            bucketName = minioConfig.getBucketName();
        }
        try {
            int length = 0;
            byte[] buffer = new byte[1024];
            out = response.getOutputStream();
            response.reset();
            response.addHeader("Content-Disposition",
                    " attachment;filename=" + URLEncoder.encode(fileName, "UTF-8"));
            response.setContentType("application/octet-stream");
            while ((length = in.read(buffer)) > 0) {
                out.write(buffer, 0, length);
            }
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            }
            if (out != null) {
                try {
                    out.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }

    }

    /**
     * @Title: getAllBuckets
     * @Description: (获取全部bucket)
     * []
     */
    public List<Bucket> getAllBuckets() throws Exception {
        return client().listBuckets();
    }

    /**
     * @param bucketName bucket名称
     * @throws IllegalArgumentException 
     * @throws XmlParserException 
     * @throws ServerException 
     * @Title: removeBucket
     * @Description: (根据bucketName删除信息)
     * [bucketName] 桶名
     */
    public void removeBucket(String bucketName) throws BaseException, InsufficientDataException, ErrorResponseException, IOException, NoSuchAlgorithmException, InvalidKeyException, InvalidResponseException, InternalException, ServerException, XmlParserException, IllegalArgumentException {
        minioClient.removeBucket(RemoveBucketArgs.builder().bucket(bucketName).build());
    }

    /**
     * @param bucketName bucket名称
     * @param objectName ⽂件名称
     * @param expires    过期时间 <=7
     * @return url
     * @Title: getObjectURL
     * @Description: (获取 ⽂ 件外链)
     * [bucketName 桶名, objectName 文件名, expires 时间<=7]
     */
    public String getObjectUrl(String bucketName, String objectName, Integer expires) throws Exception {
        if (ObjectUtil.isEmpty(expires)) {
            // 设置默认过期时间
            expires = DEFAULT_EXPIRY_TIME;
        }
        return client().getPresignedObjectUrl(GetPresignedObjectUrlArgs.builder()
                .bucket(bucketName)
                .expiry(expires)
                .object(objectName)
                .method(Method.GET)
                .build());
    }

    /**
     * @param bucketName bucket名称
     * @param objectName ⽂件名称
     * @return ⼆进制流
     * @Title: getObject
     * @Description: (获取文件)
     * [bucketName 桶名, objectName 文件名]
     */
    public InputStream getObject(String bucketName, String objectName) throws Exception {
        return client().getObject(
                GetObjectArgs
                        .builder()
                        .bucket(bucketName)
                        .object(objectName)
                        .build()
        );
    }

    /**
     * @param bucketName bucket名称
     * @param objectName ⽂件名称
     * @param stream     ⽂件流
     * @throws Exception https://docs.minio.io/cn/java-client-api-reference.html#putObject
     * @Title: putObject
     * @Description: (上传文件)
     * [bucketName 桶名, objectName 文件名, stream ⽂件流]
     */
    public void putObject(String bucketName, String objectName, InputStream stream) throws
            Exception {
        putObjectByStream(bucketName, objectName, stream);
    }

    /**
     * 上传⽂件
     *
     * @param bucketName  bucket名称
     * @param objectName  ⽂件名称
     * @param stream      ⽂件流
     * @param size        ⼤⼩
     * @param contextType 类型
     * @throws Exception https://docs.minio.io/cn/java-client-api-reference.html#putObject
     * @Title: putObject
     * @Description: $(文件流上传文件)
     * [bucketName, objectName, stream, size, contextType]
     */
    public void putObject(String bucketName, String objectName, InputStream stream, long
            size, String contextType) throws Exception {
        putObjectByStream(bucketName, objectName, stream);
    }

    /**
     * @param bucketName bucket名称
     * @param objectName ⽂件名称
     * @throws Exception https://docs.minio.io/cn/java-client-api-reference.html#statObject
     * @Title: getObjectInfo
     * @Description: (获取文件信息)
     * [bucketName, objectName]
     */
    public StatObjectResponse getObjectInfo(String bucketName, String objectName) throws Exception {
        return client().statObject(StatObjectArgs
                .builder()
                .bucket(bucketName)
                .object(objectName)
                .build());
    }

    /**
     * @param bucketName bucket名称
     * @param objectName ⽂件名称
     * @throws Exception https://docs.minio.io/cn/java-client-apireference.html#removeObject
     * @Title: removeObject
     * @Description: (删除文件)
     * [bucketName, objectName]
     */
    public void removeObject(String bucketName, String objectName) throws Exception {
        client().removeObject(RemoveObjectArgs.builder().bucket(bucketName).object(objectName).build());
    }

    /**
     * 合并文件
     *
     * @param bucketName             bucket名称
     * @param sliceFolderName        分片存储⽂件夹名称
     * @param mergeFolderAndFileName 合并存储⽂件夹名称 + "/" + 文件名称
     * @return String 文件合并的地址
     * @author zzy
     * @date 2025/12/15
     * @Param
     **/
    public String composeFilePart(String bucketName, String sliceFolderName, String mergeFolderAndFileName) {
        String mergeUrl = null;
        String fileExt = null;
        // 空值为断点续传,否则为一般的桶
        if (StringUtils.isEmpty(bucketName)) {
            bucketName = minioConfig.getBucketName();
        }
        List<ComposeSource> sourceObjectList = new ArrayList<ComposeSource>();
        try {
            List<Object> folderList = getFolderList(bucketName, sliceFolderName);
            List<String> fileNames = new ArrayList<>();
            if (CollectionUtil.isNotEmpty(folderList)) {
                for (Object value : folderList) {
                    Map o = (Map) value;
                    String name = (String) o.get("fileName");
                    if (fileExt.isEmpty()){
                        fileExt = name.substring(name.lastIndexOf("."));
                    }
                    fileNames.add(name);
                }
            }
            List<Integer> fileNameInt = new ArrayList<>();
            List<String> fileNameLast = new ArrayList<>();
            if (!fileNames.isEmpty()) {
                for (String fileName : fileNames) {
                    fileNameInt.add(Integer.parseInt(fileName.split("/")[2]));
                }
                Collections.sort(fileNameInt);
                for (int j = 0; j < fileNameInt.size(); j++) {
                    fileNameLast.add(fileNames.get(j).split("/")[0] + "/" + fileNames.get(j).split("/")[1] + "/" + fileNameInt.get(j));
                }
                for (String name : fileNameLast) {
                    sourceObjectList.add(ComposeSource.builder().bucket(bucketName).object(name).build());
                }
            }
            String mergeName = mergeFolderAndFileName + fileExt;
            minioClient.composeObject(ComposeObjectArgs.builder()
                    .bucket(bucketName)
                    .object(mergeName)
                    .sources(sourceObjectList)
                    .build());

            // 合并文件地址
            mergeUrl = minioConfig.getEndpoint() + ":" +
                    minioConfig.getPort() + "/" +
                    bucketName + "/" +
                    mergeName;
            // 合并后删除原分片文件夹
            //removeObject(bucketName, sliceFolderName + "/");


        } catch (Exception e) {
            e.printStackTrace();
        }
        return mergeUrl;
    }


    /**
     * 获得指定桶下桶中的指定文件夹下的全部文件
     *
     * @param bucketName
     * @param objectName
     * @return java.util.List<java.lang.Object>
     * @author zzy
     * @date 2025/12/12
     * @Param
     **/
    public List<Object> getFolderList(String bucketName, String objectName) throws Exception {
        String objectNames = objectName + "/";
        Iterable<Result<Item>> results = minioClient.listObjects(
                ListObjectsArgs.builder().bucket(bucketName).prefix(objectNames).recursive(false).build());
        Iterator<Result<Item>> iterator = results.iterator();
        List<Object> items = new ArrayList<>();
        String format = "{'fileName':'%s','fileSize':'%s'}";
        while (iterator.hasNext()) {
            Item item = iterator.next().get();
            items.add(JSON.parse((String.format(format, item.objectName(),
                    formatFileSize(item.size())))));
        }
        return items;
    }

    /**
     * 计算文件大小,并给与 B KB MB GB
     *
     * @param fileS 文件字节
     * @return java.lang.String
     * @author zzy
     * @date 2025/12/15
     * @Param
     **/
    public static String formatFileSize(long fileS) {
        DecimalFormat df = new DecimalFormat("#.00");
        String fileSizeString;
        String wrongSize = "0B";
        if (fileS == 0) {
            return wrongSize;
        }
        if (fileS < 1024) {
            fileSizeString = df.format((double) fileS) + " B";
        } else if (fileS < 1048576) {
            fileSizeString = df.format((double) fileS / 1024) + " KB";
        } else if (fileS < 1073741824) {
            fileSizeString = df.format((double) fileS / 1048576) + " MB";
        } else {
            fileSizeString = df.format((double) fileS / 1073741824) + " GB";
        }
        return fileSizeString;
    }

}
