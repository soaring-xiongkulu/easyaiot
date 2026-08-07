cmake_minimum_required(VERSION 3.10)

PROJECT(RUNTIME)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -pthread")
set(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g2 -ggdb")
set(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O3 -Wall")

# Optional: path to official ONNX Runtime C++ SDK (include/ + lib/)
set(ONNXRUNTIME_ROOT "" CACHE PATH "ONNX Runtime C++ SDK root")

find_package(OpenCV REQUIRED)
message(STATUS "OpenCV: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "OpenCV version: ${OpenCV_VERSION}")

find_package(CURL REQUIRED)

find_library(JSONCPP_LIBRARY NAMES jsoncpp REQUIRED)
find_library(GLOG_LIBRARY NAMES glog REQUIRED)
find_library(AVCODEC_LIBRARY NAMES avcodec REQUIRED)
find_library(AVFORMAT_LIBRARY NAMES avformat REQUIRED)
find_library(AVUTIL_LIBRARY NAMES avutil REQUIRED)
find_library(SWSCALE_LIBRARY NAMES swscale REQUIRED)
find_library(INIH_LIBRARY NAMES inih)
find_library(PUGIXML_LIBRARY NAMES pugixml)
message(STATUS "jsoncpp: ${JSONCPP_LIBRARY}")
message(STATUS "glog: ${GLOG_LIBRARY}")
message(STATUS "ffmpeg: ${AVFORMAT_LIBRARY} ${AVCODEC_LIBRARY}")

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/src/
    ${CMAKE_SOURCE_DIR}/3rdparty/cpp-httplib/
)

if(ONNXRUNTIME_ROOT)
    include_directories(
        ${ONNXRUNTIME_ROOT}/include
        ${ONNXRUNTIME_ROOT}/include/onnxruntime
        ${ONNXRUNTIME_ROOT}/include/onnxruntime/core/session
    )
    link_directories(${ONNXRUNTIME_ROOT}/lib)
    message(STATUS "ONNXRUNTIME_ROOT: ${ONNXRUNTIME_ROOT}")
else()
    include_directories(
        /usr/include
        /usr/local/include
        /usr/local/include/onnxruntime
    )
endif()

# OpenCV 5 conda layout: include/opencv5
if(DEFINED ENV{CONDA_PREFIX})
    include_directories($ENV{CONDA_PREFIX}/include/opencv5)
    link_directories($ENV{CONDA_PREFIX}/lib)
endif()

file(GLOB_RECURSE Src_SOURCES ${CMAKE_SOURCE_DIR}/src/*.cpp)
list(FILTER Src_SOURCES EXCLUDE REGEX ".*Yolov11Engine_Fixed\\.cpp$")

add_executable(${PROJECT_NAME} ${Src_SOURCES})

# Link only modules used by RUNTIME
set(OPENCV_LINK_LIBS
    opencv_core
    opencv_imgproc
    opencv_imgcodecs
    opencv_dnn
    opencv_geometry
    opencv_highgui
    opencv_videoio
)
message(STATUS "OpenCV link libs (minimal): ${OPENCV_LINK_LIBS}")

set(OPTIONAL_LIBS "")
if(INIH_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${INIH_LIBRARY})
endif()
if(PUGIXML_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${PUGIXML_LIBRARY})
endif()

target_link_libraries(${PROJECT_NAME}
    ${OPENCV_LINK_LIBS}
    ${AVFORMAT_LIBRARY}
    ${AVCODEC_LIBRARY}
    ${AVUTIL_LIBRARY}
    ${SWSCALE_LIBRARY}
    CURL::libcurl
    ${OPTIONAL_LIBS}
    ${JSONCPP_LIBRARY}
    ${GLOG_LIBRARY}
    onnxruntime
    pthread
    dl
)
