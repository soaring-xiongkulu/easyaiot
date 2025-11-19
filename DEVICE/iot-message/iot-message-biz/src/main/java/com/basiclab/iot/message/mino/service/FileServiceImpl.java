package com.basiclab.iot.message.mino.service;

import com.basiclab.iot.message.domain.model.vo.ResponseVo;
import com.basiclab.iot.message.mino.config.MinioConfig;
import io.minio.*;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.util.FastByteArrayOutputStream;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * @author zhouzhihong
 * @create 2024-09-23 22:16
 */
@Service
@Slf4j
public class FileServiceImpl implements FileService {


    @Resource
    private MinioConfig minIoConfig;

    @SneakyThrows
    @Override
    public List<String> upload(MultipartFile[] uploadFiles, HttpServletRequest request,String parentPathName) {
        return batchUpload(uploadFiles, request,parentPathName);
    }
    @SneakyThrows
    private String upload(MultipartFile file,String parentPathName) {
        return upload(file.getInputStream(), file.getOriginalFilename(), file.getSize(), file.getContentType(),parentPathName);
    }

    @Override
    public String upload(InputStream inputStream, String oldFileName, Long size, String contentType,String parentPathName) {
        // 创建MinIo的连接对象
        MinioClient minioClient = getClient();
        String bucketName = minIoConfig.getBucketName();
        try {
            // 查看桶是否存在
            BucketExistsArgs bucket = BucketExistsArgs.builder().bucket(bucketName).build();
            boolean flag = minioClient.bucketExists(bucket);
            if (!flag) {
                // 不存在则新建一个桶
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(minIoConfig.getBucketName()).build());
            }
            // 拼接新的文件名
            String newFileName = UUID.randomUUID() + oldFileName.substring(oldFileName.lastIndexOf("."));
            // 上传路径
            String objectName = parentPathName+"/"+new SimpleDateFormat("yyyy/MM/dd").format(new Date()) + "/" + newFileName;
            minioClient.putObject(
                    PutObjectArgs.builder().bucket(bucketName).object(objectName)
                            .stream(inputStream, size, -1)
                            .contentType(contentType).build()
            );
            return minIoConfig.getEndpoint()+":"+minIoConfig.getPort()+"/"+minIoConfig.getBucketName()+"/"+ objectName;
        } catch (Exception e) {
            e.printStackTrace();
            return "上传失败！";
        } finally {
            if (inputStream != null) {
                try {
                    inputStream.close();
                } catch (IOException e) {
                    log.error("inputStream close IOException:" + e.getMessage());
                }
            }
        }
    }

    @Override
    public void download(String fileName, HttpServletResponse response) {
        GetObjectArgs objectArgs = GetObjectArgs.builder().bucket(minIoConfig.getBucketName()).object(fileName).build();
        try (GetObjectResponse resp = getClient().getObject(objectArgs)) {
            byte[] buf = new byte[1024];
            int len;
            try (FastByteArrayOutputStream os = new FastByteArrayOutputStream()) {

                while ((len = resp.read(buf)) != -1) {
                    os.write(buf, 0, len);
                }
                os.flush();
                byte[] bytes = os.toByteArray();
                response.setCharacterEncoding("utf-8");
                response.addHeader("Content-Disposition", "attachMent;fileName=" + fileName);
                try (ServletOutputStream stream = response.getOutputStream()) {
                    stream.write(bytes);
                    stream.flush();
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // 批量获取文件字符数组
    @Override
    public Map<String,byte[]> getFileList(List<String> fileNames) {
        if(CollectionUtils.isEmpty(fileNames)){
            return null;
        }
        Map<String,byte[]> map=new HashMap<>(fileNames.size());
        fileNames.forEach(fileName->{
            GetObjectArgs objectArgs = GetObjectArgs.builder().bucket(minIoConfig.getBucketName()).object(fileName).build();
            try (GetObjectResponse resp = getClient().getObject(objectArgs)) {
                byte[] buf = new byte[1024];
                int len;
                try (FastByteArrayOutputStream os = new FastByteArrayOutputStream()) {

                    while ((len = resp.read(buf)) != -1) {
                        os.write(buf, 0, len);
                    }
                    os.flush();
                    map.put(fileName,os.toByteArray());
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
        return map;
    }

    @Override
    public byte[] getFileBytes(String fileName) {
        byte[] bytes = new byte[0];
        GetObjectArgs objectArgs = GetObjectArgs.builder().bucket(minIoConfig.getBucketName()).object(fileName).build();
        try (GetObjectResponse resp = getClient().getObject(objectArgs)) {
            byte[] buf = new byte[1024];
            int len;
            try (FastByteArrayOutputStream os = new FastByteArrayOutputStream()) {

                while ((len = resp.read(buf)) != -1) {
                    os.write(buf, 0, len);
                }
                os.flush();
                bytes = os.toByteArray();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return bytes;
    }

    @Override
    public void remove(String url) {
        String objName = url.substring(url.lastIndexOf("/") + minIoConfig.getBucketName().length() + 1);
        try {
            getClient().removeObject(RemoveObjectArgs.builder().bucket(minIoConfig.getBucketName()).object(objName).build());
        } catch (Exception e) {
            e.printStackTrace();
        }
    }




    @Override
    public ResponseVo<String> upload(MultipartFile uploadFiles, HttpServletRequest request, String parentPathName) {
        ResponseVo<String> responseVo = new ResponseVo<>();
        String fileName = "";
        //上传图片限制大小
        Long len = uploadFiles.getSize();
        //上传实际方法
        if (uploadFiles.getSize() != 0) {
            fileName = upload(uploadFiles,parentPathName);
        }
        //上传成功
        responseVo.setData(fileName);
        responseVo.setMessage("上传成功");
        responseVo.setStatus(200);
        return responseVo;
    }

    private boolean checkFileSize(Long len, int size) {
        double fileSize = 0;
        fileSize = (double) len / 1048576;
        if (fileSize > size) {
            return false;
        }
        return true;
    }

    @Override
    public List<String> batchUpload(MultipartFile[] uploadFiles, HttpServletRequest request,String parentPathName) {
        List<String> urls = new ArrayList<>();
        for (MultipartFile multipartFile : uploadFiles) {
            singleFileUpload(urls, multipartFile,parentPathName);
        }
        return urls;
    }

    private void singleFileUpload(List<String> urls, MultipartFile multipartFile,String parentPathName) {
        String url = upload(multipartFile,parentPathName);
        urls.add(url);
    }

    @Override
    public void redirectTo(HttpServletRequest req, HttpServletResponse response) {
        try {
            String bucketName = req.getParameter("bucketName");
            String objectName = req.getParameter("objectName");
            String url = minIoConfig.getEndpoint() + ":" +
                    minIoConfig.getPort() + "/" +
                    bucketName + "/" +
                    objectName;
            URL urls = new URL(url);
            HttpURLConnection conn = (HttpURLConnection)urls.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(50 * 1000);
            conn.setReadTimeout(50 * 1000);
            InputStream inStream = conn.getInputStream();
            ByteArrayOutputStream outStream = new ByteArrayOutputStream();
            byte[] buffer = new byte[2048];
            int len = 0;
            while( (len=inStream.read(buffer)) != -1 ){
                outStream.write(buffer, 0, len);
            }
            inStream.close();
            byte data[] = outStream.toByteArray();
            if (objectName.endsWith("pdf")) {
                response.setContentType("application/pdf");
            } else {
                response.setContentType("image/jpg");
            }
            OutputStream os = response.getOutputStream();
            os.write(data);
            os.flush();
            os.close();
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private MinioClient getClient() {
        MinioClient minioClient = MinioClient.builder().endpoint(minIoConfig.getEndpoint() + ":" + minIoConfig.getPort()).credentials(minIoConfig.getAccessKey(), minIoConfig.getSecretKey()).build();
        return minioClient;
    }
}



