cmake_minimum_required(VERSION 3.5)

PROJECT (TASK)

set(CMAKE_CXX_STANDARD 17)

# 平台判断
if(WIN32)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /std:c++17")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -pthread")
endif()

set(CMAKE_BUILD_TYPE DEBUG)

if(MSVC)
    SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /W4 /Zi")
    SET(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2 /W4")
else()
    SET(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g2 -ggdb")
    SET(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O3 -Wall")
endif()

# 查找依赖库
find_package(OpenCV REQUIRED)
message(STATUS "OpenCV: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "${OpenCV_VERSION}")

find_package(CURL REQUIRED)

# Windows下使用find_package，Linux下使用find_library
if(WIN32)
    find_package(jsoncpp REQUIRED)
    find_package(glog REQUIRED)
    # Windows下需要手动查找FFmpeg库
    find_library(AVCODEC_LIBRARY avcodec REQUIRED)
    find_library(AVFORMAT_LIBRARY avformat REQUIRED)
    find_library(AVUTIL_LIBRARY avutil REQUIRED)
    find_library(SWSCALE_LIBRARY swscale REQUIRED)
    message(STATUS "FFmpeg libraries found")
else()
    # Linux下使用find_library查找jsoncpp和glog
    # 尝试多个可能的库名
    find_library(JSONCPP_LIBRARY 
        NAMES jsoncpp libjsoncpp.so.25 libjsoncpp.so.1.9.5
        PATHS /usr/lib /usr/lib/x86_64-linux-gnu /lib /lib/x86_64-linux-gnu
        REQUIRED
    )
    find_library(GLOG_LIBRARY 
        NAMES glog libglog.so.1 libglog.so.0.6.0
        PATHS /usr/lib /usr/lib/x86_64-linux-gnu /lib /lib/x86_64-linux-gnu
        REQUIRED
    )
    find_library(INIH_LIBRARY
        NAMES inih libinih.so.1 libinih.so.55
        PATHS /usr/lib /usr/lib/x86_64-linux-gnu /lib /lib/x86_64-linux-gnu
        REQUIRED
    )
    find_library(PUGIXML_LIBRARY
        NAMES pugixml libpugixml.so.1 libpugixml.so.1.14
        PATHS /usr/lib /usr/lib/x86_64-linux-gnu /lib /lib/x86_64-linux-gnu
        REQUIRED
    )
    message(STATUS "jsoncpp library: ${JSONCPP_LIBRARY}")
    message(STATUS "glog library: ${GLOG_LIBRARY}")
    message(STATUS "inih library: ${INIH_LIBRARY}")
    message(STATUS "pugixml library: ${PUGIXML_LIBRARY}")
endif()

# Windows平台使用ONNX Runtime DirectML (支持RTX 5060)
if(WIN32)
    # 混合方案：vcpkg头文件 + Python DirectML DLL
    set(PYTHON_ONNXRUNTIME "G:/anaconda/envs/easyaiot/Lib/site-packages/onnxruntime")
    set(VCPKG_ROOT "F:/EASYLOT/vcpkg-master/installed/x64-windows")
    
    # 添加UTF-8编码支持
    add_compile_options("$<$<C_COMPILER_ID:MSVC>:/utf-8>")
    add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/utf-8>")
    
    include_directories(
        ${OpenCV_INCLUDE_DIRS}
        ${CMAKE_SOURCE_DIR}/src/
        ${CMAKE_SOURCE_DIR}/3rdparty/cpp-httplib/
        # ONNX Runtime头文件（从vcpkg）
        ${VCPKG_ROOT}/include
        ${VCPKG_ROOT}/include/onnxruntime
    )
    
    link_directories(
        # ONNX Runtime DirectML库文件（从Python，运行时加载）
        ${PYTHON_ONNXRUNTIME}/capi
        # vcpkg库文件（编译时链接）
        ${VCPKG_ROOT}/lib
    )
else()
    # Linux平台
    link_directories(
        /usr/lib/
        /usr/local/lib/
        /usr/local/openssl/lib
    )

    include_directories(
        /usr/include/
        /usr/local/include
        /usr/local/include/onnxruntime
        /usr/local/openvino/3rdparty/jsoncpp/include
        # 优先使用系统的OpenCV头文件，确保与链接的库版本匹配
        ${OpenCV_INCLUDE_DIRS}
        # 使用OpenVINO的OpenCV头文件（作为备选）
        /usr/local/openvino/3rdparty/opencv/include
        ${CMAKE_SOURCE_DIR}/src/
        ${CMAKE_SOURCE_DIR}/3rdparty/cpp-httplib/
    )
    
    # 不定义OpenCV版本宏，让OpenCV自己定义版本
    # 移除硬编码版本定义以避免与OpenVINO的OpenCV 4.7冲突
endif()

# 收集所有源文件
file (GLOB Src_SOURCES ${CMAKE_SOURCE_DIR}/src/*.cpp)

# 根据平台排除特定文件
if(WIN32)
    # Windows平台排除Linux版本和Fixed文件
    list(FILTER Src_SOURCES EXCLUDE REGEX ".*Yolov11ThreadPool\\.cpp$")
    list(FILTER Src_SOURCES EXCLUDE REGEX ".*Yolov11Engine_Fixed\\.cpp$")
else()
    # Linux平台排除Windows版本和Fixed文件
    list(FILTER Src_SOURCES EXCLUDE REGEX ".*Yolov11ThreadPool_Windows\\.cpp$")
    list(FILTER Src_SOURCES EXCLUDE REGEX ".*Yolov11Engine_Fixed\\.cpp$")
endif()

add_executable(${PROJECT_NAME} ${Src_SOURCES})

# 链接库
if(WIN32)
    target_link_libraries(${PROJECT_NAME}
        ${OpenCV_LIBS}
        # FFmpeg库
        ${AVFORMAT_LIBRARY}
        ${AVCODEC_LIBRARY}
        ${AVUTIL_LIBRARY}
        ${SWSCALE_LIBRARY}
        # CURL
        CURL::libcurl
        # jsoncpp
        jsoncpp_lib
        # glog
        glog::glog
        # ONNX Runtime (vcpkg) - 直接链接库文件
        onnxruntime
        # Windows系统库
        ws2_32
        bcrypt
    )
else()
    # Linux链接
    # 使用pkg-config获取完整的OpenCV库列表
    execute_process(
        COMMAND pkg-config --libs opencv4
        OUTPUT_VARIABLE OPENCV_PKG_LIBS
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    message(STATUS "OpenCV pkg-config libs: ${OPENCV_PKG_LIBS}")
    
    target_link_libraries(${PROJECT_NAME}
        ${OPENCV_PKG_LIBS}
        avformat avcodec avutil swscale
        png z
        curl
        crypto ssl
        ${INIH_LIBRARY}
        ${PUGIXML_LIBRARY}
        ${JSONCPP_LIBRARY}
        ${GLOG_LIBRARY}
        onnxruntime
        pthread
    )
endif()
