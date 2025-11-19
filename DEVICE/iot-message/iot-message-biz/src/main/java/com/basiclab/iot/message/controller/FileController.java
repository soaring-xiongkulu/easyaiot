package com.basiclab.iot.message.controller;


import com.basiclab.iot.message.domain.model.vo.ResponseVo;
import com.basiclab.iot.message.mino.service.FileService;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * 协议文件上传下载工具类
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 * @since 2024-07-17
 */
@Slf4j
@RestController
@RequestMapping("/message/file")
@Tag(name  ="文件上传")
public class FileController {

    private static final String FILE_PATH = "annex";
    @Autowired
    private FileService fileService;

    /**
     * 将文件保存到指定文件夹
     *
     * @param file 单个文件
     * @return 重定向到controller层中前往下载页面的url
     * @throws IOException
     */
    @PostMapping("/upload")
    @ApiOperation("将文件保存到指定文件夹")
    public Map<String, String> uploadAndGoDownLoad(HttpServletRequest request, @RequestPart("file") MultipartFile file) throws IOException {
//        String newFileName = "";
//        //判断文件是否为空，不为空时，保存文件
//        if (!file.isEmpty()) {
//            try {
//                newFileName = fileUtils.uploadFile(file, FILE_PATH);
//            } catch (Exception e) {
//                throw new RuntimeException(e);
//            }
//        }
        ResponseVo<String> responseVo = fileService.upload(file,request,FILE_PATH);
        String newFileName = responseVo.getData();

        log.info("annex file upload to down load path is:"+newFileName);
        Map<String,String> map = new HashMap<>();
        map.put("filePath",newFileName);
        map.put("fileName",file.getOriginalFilename());
        return map;
    }

    /**
     * 使用Hutool实现文件下载
     *
     * @param fileName 要下载的文件名
     * @param response
     */
    @GetMapping("/download/hutool")
    @ResponseBody
    @ApiOperation("使用Hutool实现文件下载")
    public void downloadByHutool(@RequestParam(value = "fileName") String fileName,
                                 HttpServletResponse response) {
//        //防止中文乱码
//        response.setCharacterEncoding("UTF-8");
//        ApplicationHome applicationHome = new ApplicationHome(this.getClass());
//        String path = applicationHome.getDir().getParentFile().getParentFile().getAbsolutePath() + FILE_PATH;
//        //获取文件
//        File file = new File(path+fileName);
//        ServletUtil.write(response, file);
        fileService.download(fileName,response);
    }

}