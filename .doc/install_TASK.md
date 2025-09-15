# TASK模块部署文档

## 安装第三方库
```shell
git clone https://github.com/ZLMediaKit/ZLMediaKit.git
git clone https://github.com/rockchip-linux/mpp.git

cd /submodules/ZLMediaKit
git submodule init
git submodule update
cmake . -B build && cmake --build build
cd /submodules/mpp
cmake . -B build && cmake --build build
 
cp ./submodules/ZLMediaKit/release/linux/Debug/libmk_api.so zl_mpp_libs/
cp ./submodules/mpp/build/utils/libutils.a zl_mpp_libs/ffmpeg
```

## 编译项目代码
说明：`yolov8_single_camera.cpp` 支持完整单路拉流推理推流
`yolov8_multiple_camera.cpp` 支持最高8路拉流推理，但不支持推流，在此之前你需要修改代码中的rtsp地址，以及进行进路拉流测试。
```shell
cmake -S . -B build && cmake --build build
```

## 启动测试
```shell
# 针对 yolov8_single_camera.cpp
./build/yolov8_single_camera <model path> <rtsp url> <264/265>

# 针对 yolov8_multiple_camera.cpp
./build/yolov8_multiple_camera
```

