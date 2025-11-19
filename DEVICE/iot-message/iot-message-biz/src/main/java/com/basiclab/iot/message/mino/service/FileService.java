package com.basiclab.iot.message.mino.service;

import com.basiclab.iot.message.domain.model.vo.ResponseVo;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.InputStream;
import java.util.List;
import java.util.Map;

/**
 * @author zhouzhihong
 * @create 2024-09-23 22:15
 */

public interface FileService {

    List<String> upload(MultipartFile[] uploadFiles, HttpServletRequest request,String parentPathName);

    ResponseVo<String> upload(MultipartFile uploadFiles, HttpServletRequest request, String parentPathName);

    String upload(InputStream inputStream, String oldFileName, Long size, String contentType,String parentPathName);

    /**
     * 文件下载
     * @param fileName
     * @param response
     */
    void download(String fileName, HttpServletResponse response);

    /**
     * 文件下载
     * @param fileName
     */
    byte[]  getFileBytes(String fileName);

     Map<String,byte[]> getFileList(List<String> fileNames);


        void remove(String url);


    List<String> batchUpload(MultipartFile[] uploadFiles, HttpServletRequest request,String parentPathName);

    void redirectTo(HttpServletRequest req, HttpServletResponse response);
}
