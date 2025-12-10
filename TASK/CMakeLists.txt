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
find_package(jsoncpp REQUIRED)
find_package(glog REQUIRED)

# Windows下需要手动查找FFmpeg库
if(WIN32)
    find_library(AVCODEC_LIBRARY avcodec REQUIRED)
    find_library(AVFORMAT_LIBRARY avformat REQUIRED)
    find_library(AVUTIL_LIBRARY avutil REQUIRED)
    find_library(SWSCALE_LIBRARY swscale REQUIRED)
    message(STATUS "FFmpeg libraries found")
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
        ${OpenCV_INCLUDE_DIRS}
        ${CMAKE_SOURCE_DIR}/src/
        ${CMAKE_SOURCE_DIR}/3rdparty/cpp-httplib/
    )
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
    target_link_libraries(${PROJECT_NAME}
        ${OpenCV_LIBS}
        avformat avcodec avutil
        png z
        curl curlpp
        crypto ssl
        inih INIReader
        pugixml
        jsoncpp
        glog
        onnxruntime
        pthread
    )
endif()
