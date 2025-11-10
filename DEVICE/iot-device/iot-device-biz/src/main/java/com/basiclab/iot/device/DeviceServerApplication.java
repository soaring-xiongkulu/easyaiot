package com.basiclab.iot.device;

import com.basiclab.iot.common.annotation.EnableCustomSwagger2;
import com.basiclab.iot.common.annotations.EnableCustomConfig;
import com.basiclab.iot.common.annotations.EnableRyFeignClients;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.CrossOrigin;

import java.io.IOException;

/**
 * 项目的启动类
 * <p>
 *
 * @author 翱翔的雄库鲁
 * @email andywebjava@163.com
 * @wechat EasyAIoT2025
 */
@EnableCustomConfig
@EnableCustomSwagger2
@EnableRyFeignClients
@CrossOrigin(origins = "*", maxAge = 3600)
@Slf4j
@SpringBootApplication(scanBasePackages = {"com.basiclab.iot"})
public class DeviceServerApplication {

    static {
        // 加载OpenCV本机库
//        System.load("/projects/opencv-4.10.0/install/share/java/opencv4/libopencv_java4100.so");
//        System.load("");
//        System.load("/projects/opencv-4.10.0/install/share/java/opencv4/opencv-4100.jar");
    }

    public static void main(String[] args) throws IOException {
//        // 检查OpenCV库是否成功加载
//        if (Core.VERSION_MAJOR == 4) {
//            System.out.println("OpenCV库已成功加载！版本号为：" + Core.VERSION_MAJOR);
//        } else {
//            System.out.println("OpenCV库加载失败！");
//        }
//        String os = System.getProperty("os.name", "generic").toLowerCase(Locale.ENGLISH);
//        System.out.println("os：" + os);
//        String arch = System.getProperty("os.arch", "generic").toLowerCase(Locale.ENGLISH);
//        System.out.println("arch：" + arch);
//        // TODO: Switch this to Path.of when the minimum Java version is 11.
//        // /data/projects/onnxruntime/native/linux-x64/libonnxruntime.so
//        String libraryDirPathProperty = "/data/projects/onnxruntime/native/linux-x64";
//        String libraryFileName = "libonnxruntime.so";
//        File libraryFile = Paths.get(libraryDirPathProperty, libraryFileName).toFile();
//        String libraryFilePath = libraryFile.getAbsolutePath();
//        if (!libraryFile.exists()) {
//            throw new IOException("Native library '" + libraryFileName + "' not found at " + libraryFilePath);
//        }
//        System.load(libraryFilePath);
//        System.out.println("Loaded native library '" + libraryFileName + "' from specified path");
        SpringApplication.run(DeviceServerApplication.class, args);
    }
}
