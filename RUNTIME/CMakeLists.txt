cmake_minimum_required(VERSION 3.10)

PROJECT(RUNTIME)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# --- platform flags (Linux keeps pthread; MSVC uses default CRT threads) ---
if(WIN32)
    if(MSVC)
        add_compile_definitions(WIN32_LEAN_AND_MEAN NOMINMAX _CRT_SECURE_NO_WARNINGS GLOG_NO_ABBREVIATED_SEVERITIES GLOG_USE_GLOG_EXPORT)
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /std:c++17 /EHsc /W3 /utf-8")
        set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /Od /Zi")
        set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2")
    endif()
    set(RUNTIME_VENDOR_ROOT "${CMAKE_SOURCE_DIR}/vendor/win-x64"
        CACHE PATH "Windows vendor root (ORT/OpenCV/FFmpeg DLL layout)")
    if(NOT ONNXRUNTIME_ROOT)
        set(ONNXRUNTIME_ROOT "${RUNTIME_VENDOR_ROOT}/onnxruntime"
            CACHE PATH "ONNX Runtime C++ SDK root" FORCE)
    endif()
    # conda-forge win-64: headers/libs under Library/
    if(DEFINED ENV{CONDA_PREFIX})
        list(APPEND CMAKE_PREFIX_PATH "$ENV{CONDA_PREFIX}/Library")
    endif()
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -pthread")
    set(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g2 -ggdb")
    set(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O3 -Wall")
endif()

# Optional: path to official ONNX Runtime C++ SDK (include/ + lib/)
if(NOT ONNXRUNTIME_ROOT)
    set(ONNXRUNTIME_ROOT "" CACHE PATH "ONNX Runtime C++ SDK root")
endif()

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

# find_library does not always export include dirs on Windows (conda-forge layout).
if(WIN32)
    if(JSONCPP_LIBRARY)
        get_filename_component(_JSONCPP_LIB_DIR "${JSONCPP_LIBRARY}" DIRECTORY)
        include_directories("${_JSONCPP_LIB_DIR}/../include")
    endif()
    if(AVFORMAT_LIBRARY)
        get_filename_component(_FFMPEG_LIB_DIR "${AVFORMAT_LIBRARY}" DIRECTORY)
        include_directories("${_FFMPEG_LIB_DIR}/../include")
    endif()
    if(GLOG_LIBRARY)
        get_filename_component(_GLOG_LIB_DIR "${GLOG_LIBRARY}" DIRECTORY)
        include_directories("${_GLOG_LIB_DIR}/../include")
    endif()
endif()

if(ONNXRUNTIME_ROOT)
    include_directories(
        ${ONNXRUNTIME_ROOT}/include
        ${ONNXRUNTIME_ROOT}/include/onnxruntime
        ${ONNXRUNTIME_ROOT}/include/onnxruntime/core/session
    )
    link_directories(${ONNXRUNTIME_ROOT}/lib)
    message(STATUS "ONNXRUNTIME_ROOT: ${ONNXRUNTIME_ROOT}")
else()
    if(WIN32)
        message(WARNING "ONNXRUNTIME_ROOT not set; run scripts/fetch_deps_windows.ps1 or pass -DONNXRUNTIME_ROOT=...")
    else()
        include_directories(
            /usr/include
            /usr/local/include
            /usr/local/include/onnxruntime
        )
    endif()
endif()

# OpenCV 5 conda layout: include/opencv5
if(DEFINED ENV{CONDA_PREFIX})
    include_directories($ENV{CONDA_PREFIX}/include/opencv5)
    link_directories($ENV{CONDA_PREFIX}/lib)
    if(WIN32)
        include_directories($ENV{CONDA_PREFIX}/Library/include/opencv4)
        link_directories($ENV{CONDA_PREFIX}/Library/lib)
    endif()
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
    opencv_highgui
    opencv_videoio
)
# opencv_geometry is OpenCV 5+; pointPolygonTest lives in imgproc (OpenCV 4.x).
message(STATUS "OpenCV link libs (minimal): ${OPENCV_LINK_LIBS}")

set(OPTIONAL_LIBS "")
if(INIH_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${INIH_LIBRARY})
endif()
if(PUGIXML_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${PUGIXML_LIBRARY})
endif()

set(PLATFORM_LIBS "")
if(WIN32)
    list(APPEND PLATFORM_LIBS ws2_32)
else()
    list(APPEND PLATFORM_LIBS pthread dl)
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
    ${PLATFORM_LIBS}
)

# Windows: copy ORT runtime DLL next to RUNTIME.exe when using vendor layout
if(WIN32 AND ONNXRUNTIME_ROOT)
    set(_ORT_DLL "${ONNXRUNTIME_ROOT}/lib/onnxruntime.dll")
    if(EXISTS "${_ORT_DLL}")
        add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${_ORT_DLL}"
                "$<TARGET_FILE_DIR:${PROJECT_NAME}>/onnxruntime.dll"
            COMMENT "Copy onnxruntime.dll beside RUNTIME.exe")
    endif()
endif()
