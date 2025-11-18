package com.basiclab.iot.file.controller;

import com.basiclab.iot.common.domain.R;
import com.basiclab.iot.common.utils.file.FileUtils;
import com.basiclab.iot.file.config.MinioConfig;
import com.basiclab.iot.file.domain.qo.SysFileQo;
import com.basiclab.iot.file.domain.vo.BucketVo;
import com.basiclab.iot.file.domain.vo.SysFileVo;
import com.basiclab.iot.file.service.ISysFileService;
import com.github.pagehelper.PageInfo;
import io.minio.messages.DeleteObject;
import io.swagger.annotations.ApiOperation;
import io.swagger.annotations.ApiParam;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 文件请求处理
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@Tag(name = "文件管理")
@RestController
@RequestMapping("/sysFile")
public class SysFileController {
    private static final Logger log = LoggerFactory.getLogger(SysFileController.class);

    @Qualifier("getSysFileService")
    @Autowired
    private ISysFileService sysFileService;

    /**
     * 文件上传请求
     *
     * @param file
     * @return
     */
    @PostMapping("/upload")
    @ApiOperation("文件上传请求")
    public R<SysFileVo> upload(@ApiParam("设备上报实体") MultipartFile file) {
        try {
            // 上传并返回访问地址
            String url = sysFileService.uploadFile(file);
            SysFileVo sysFile = new SysFileVo();
            sysFile.setName(FileUtils.getName(url));
            sysFile.setUrl(url);
            return R.ok(sysFile);
        } catch (Exception e) {
            log.error("上传文件失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 文件上传请求（根据桶名称）
     *
     * @param file
     * @return
     */
    @PostMapping("/uploadByBucket")
    @ApiOperation("文件上传请求（根据桶名称）")
    public R<SysFileVo> uploadByBucket(@RequestParam(value = "bucketName") String bucketName, @RequestParam(value = "file") MultipartFile file) {
        try {
            // 上传并返回访问地址
            String url = sysFileService.uploadFile(file, bucketName);
            SysFileVo sysFile = new SysFileVo();
            sysFile.setName(FileUtils.getName(url));
            sysFile.setUrl(url);
            return R.ok(sysFile);
        } catch (Exception e) {
            log.error("上传文件失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 判断文件是否存在
     *
     * @param bucketName
     * @param fileName
     * @return
     */
    @PostMapping(value = "/objectExists")
    @ApiOperation("判断文件是否存在")
    R<Boolean> objectExists(String bucketName, String fileName) {
        try {
            boolean ret = sysFileService.objectExists(bucketName, fileName);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("判断文件是否存在失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 批量删除文件
     *
     * @param bucketName
     * @param list
     * @return
     */
    @PostMapping(value = "/deletes")
    @ApiOperation("批量删除文件")
    R<Boolean> deletes(String bucketName, List<DeleteObject> list) {
        try {
            boolean ret = sysFileService.deletes(bucketName, list);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("删除文件失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 删除文件
     *
     * @param bucketName
     * @param objectName
     */
    @DeleteMapping(value = "/delete")
    @ApiOperation("删除文件")
    R<Boolean> delete(@RequestParam("bucketName") String bucketName, @RequestParam("objectName") String objectName) {
        try {
            boolean ret = sysFileService.delete(bucketName, objectName);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("删除文件失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 删除文件
     *
     * @param params
     * @return
     */
    @PostMapping(value = "/removeFile")
    @ApiOperation("删除文件")
    public R<String> removeFile(@RequestBody Map<String, Object> params) {
        try {
            String bucketName = (String) params.get("bucketName");
            String objectName = (String) params.get("objectName");
            sysFileService.removeFile(bucketName, objectName);
            return R.ok("删除文件成功");
        } catch (Exception e) {
            log.error("删除文件失败", e);
            return R.fail("删除文件失败");
        }
    }

    /**
     * 获取配置文件
     *
     * @return
     */
    @PostMapping(value = "/getDataConfig")
    @ApiOperation("获取配置文件")
    public R<Object> getDataConfig() {
        try {
            Object config = sysFileService.getConfig();
            MinioConfig minioConfig = (MinioConfig) config;
            //解决返回对香包含spring管理的bean问题（MinioClient）
            HashMap<Object, Object> params = new HashMap<>();
            params.put("url", minioConfig.getUrl());
            params.put("bucketName", minioConfig.getBucketName());
            params.put("accessKey", minioConfig.getAccessKey());
            params.put("secretKey", minioConfig.getSecretKey());
            return R.ok(params, "获取配置文件成功");
        } catch (Exception e) {
            log.error("获取配置文件失败", e);
            return R.fail("获取配置文件失败");
        }
    }

    /**
     * 判断Bucket是否存在
     *
     * @param bucketName
     * @return
     */
    @PostMapping(value = "/bucketExists")
    @ApiOperation("判断Bucket是否存在")
    R<Boolean> bucketExists(@RequestBody String bucketName) {
        try {
            boolean ret = sysFileService.bucketExists(bucketName);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("判断bucket是否存在失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 创建桶
     *
     * @param bucketName
     * @return
     */
    @PostMapping(value = "/createBucket")
    @ApiOperation("创建桶")
    R<Boolean> createBucket(@RequestBody String bucketName) {
        try {
            boolean ret = sysFileService.createBucket(bucketName);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("创建桶失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 删除桶
     *
     * @param bucketName
     * @return
     * @throws Exception
     */
    @PostMapping(value = "/removeBucket")
    @ApiOperation("删除桶")
    R<Boolean> removeBucket(@RequestBody String bucketName) throws Exception {
        try {
            sysFileService.removeBucket(bucketName);
            return R.ok(true);
        } catch (Exception e) {
            log.error("删除桶失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 获取所有bucket信息
     *
     * @param sysFileQo
     * @return
     */
    @PostMapping(value = "/getAllBuckets")
    @ApiOperation("获取所有bucket信息")
    R<PageInfo<BucketVo>> getAllBuckets(@RequestBody SysFileQo sysFileQo) {
        try {
            PageInfo<BucketVo> ret = sysFileService.getAllBuckets(sysFileQo.getBucketName(), sysFileQo.getPrefix(), sysFileQo.getKey(),
                    sysFileQo.getPageNo(), sysFileQo.getPageSize());
            return R.ok(ret);
        } catch (Exception e) {
            log.error("获取所有bucket信息失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 获取某个bucket中所有的文件名
     *
     * @param sysFileQo
     * @return
     */
    @PostMapping(value = "/getFileList")
    @ApiOperation("获取某个bucket中所有的文件名")
    R<PageInfo<Map<String, Object>>> getFileList(@RequestBody SysFileQo sysFileQo) {
        try {
            PageInfo<Map<String, Object>> ret = sysFileService.getFileList(sysFileQo.getBucketName(), sysFileQo.getPrefix(), sysFileQo.getKey(),
                    sysFileQo.getPageNo(), sysFileQo.getPageSize());
            return R.ok(ret);
        } catch (Exception e) {
            log.error("获取某个bucket中所有的文件名失败", e);
            return R.fail(e.getMessage());
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
    @PostMapping(value = "/download")
    @ApiOperation("直接下载")
    R<Boolean> download(@RequestBody String bucketName, @RequestBody String objectName, @RequestBody String fileName) {
        try {
            boolean ret = sysFileService.download(bucketName, objectName, fileName);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("直接下载失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 判断文件夹是否存在
     *
     * @param bucketName
     * @param prefix
     * @return
     * @throws Exception
     */
    @PostMapping(value = "/folderExists")
    @ApiOperation("判断文件夹是否存在")
    R<Boolean> folderExists(@RequestBody String bucketName, @RequestBody String prefix) throws Exception {
        try {
            boolean ret = sysFileService.folderExists(bucketName, prefix);
            return R.ok(ret);
        } catch (Exception e) {
            log.error("判断文件夹是否存在失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 创建文件夹
     *
     * @param bucketName 桶名称
     * @param path       路径
     */
    @PostMapping(value = "/createFolder")
    @ApiOperation("创建文件夹")
    R<Boolean> createFolder(@RequestBody String bucketName, @RequestBody String path) throws Exception {
        try {
            sysFileService.folderExists(bucketName, path);
            return R.ok(true);
        } catch (Exception e) {
            log.error("创建文件夹失败", e);
            return R.fail(e.getMessage());
        }
    }

    /**
     * 获取文件在Minio在服务器上的外链
     *
     * @param objectName
     * @param bucketName
     * @return
     * @throws Exception
     */
    @PostMapping(value = "/getUrl")
    @ApiOperation("获取文件在Minio在服务器上的外链")
    R<String> getUrl(@RequestBody String objectName, @RequestBody String bucketName) throws Exception {
        try {
            String url = sysFileService.getUrl(bucketName, objectName);
            return R.ok(url);
        } catch (Exception e) {
            log.error("获取文件在minio在服务器上的外链失败", e);
            return R.fail(e.getMessage());
        }
    }
}