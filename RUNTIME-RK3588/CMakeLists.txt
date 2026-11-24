cmake_minimum_required(VERSION 3.16)

project(RUNTIME_RK3588 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

include(CheckCXXCompilerFlag)
include(CheckIPOSupported)
include(CTest)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# This module is intentionally not portable. A successful configure means the
# resulting binary can only target an RK3588-class aarch64 Linux device.
string(TOLOWER "${CMAKE_SYSTEM_PROCESSOR}" EASYAIOT_PROCESSOR)
if(NOT EASYAIOT_PROCESSOR MATCHES "^(aarch64|arm64)$")
    message(FATAL_ERROR
        "RUNTIME-RK3588 only supports RK3588/aarch64. "
        "Use an aarch64 RK3588 toolchain or configure directly on the box.")
endif()

set(ROCKCHIP_SDK_ROOT "" CACHE PATH "Rockchip RKNN/RGA/MPP SDK root")
set(RUNTIME_VERSION_STR "unknown" CACHE STRING "Runtime version")

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs geometry highgui videoio)
find_package(CURL REQUIRED)
find_package(glog CONFIG QUIET)
if(TARGET glog::glog)
    set(GLOG_LINK_LIBS glog::glog)
else()
    find_library(GLOG_LIBRARY NAMES glog REQUIRED)
    set(GLOG_LINK_LIBS ${GLOG_LIBRARY})
endif()

find_library(JSONCPP_LIBRARY NAMES jsoncpp REQUIRED)
find_library(AVCODEC_LIBRARY NAMES avcodec REQUIRED)
find_library(AVFORMAT_LIBRARY NAMES avformat REQUIRED)
find_library(AVUTIL_LIBRARY NAMES avutil REQUIRED)
find_library(INIH_LIBRARY NAMES inih)
find_library(PUGIXML_LIBRARY NAMES pugixml)

set(ROCKCHIP_HINTS
    ${ROCKCHIP_SDK_ROOT}
    ${ROCKCHIP_SDK_ROOT}/rknpu2/runtime/Linux/librknn_api
    ${ROCKCHIP_SDK_ROOT}/rknpu2/runtime/Linux/librknn_api/aarch64
    ${ROCKCHIP_SDK_ROOT}/librga
    ${ROCKCHIP_SDK_ROOT}/mpp
    /usr /usr/local /opt/rockchip /opt/rknn
)

find_path(RKNN_INCLUDE_DIR rknn_api.h
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES include rknpu2/runtime/Linux/librknn_api/include)
find_library(RKNN_LIBRARY NAMES rknnrt
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES lib lib64 aarch64)
find_path(RGA_INCLUDE_DIR im2d.hpp
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES include include/rga)
find_library(RGA_LIBRARY NAMES rga
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES lib lib64)
find_path(MPP_INCLUDE_DIR rk_mpi.h
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES include include/rockchip mpp/inc)
find_library(MPP_LIBRARY NAMES rockchip_mpp mpp
    HINTS ${ROCKCHIP_HINTS}
    PATH_SUFFIXES lib lib64)

foreach(required_var RKNN_INCLUDE_DIR RKNN_LIBRARY RGA_INCLUDE_DIR RGA_LIBRARY MPP_INCLUDE_DIR MPP_LIBRARY)
    if(NOT ${required_var})
        message(FATAL_ERROR
            "Missing required Rockchip dependency ${required_var}. "
            "Install RKNN Runtime, librga and MPP, or set ROCKCHIP_SDK_ROOT.")
    endif()
endforeach()

message(STATUS "RKNN: ${RKNN_INCLUDE_DIR} ${RKNN_LIBRARY}")
message(STATUS "RGA:  ${RGA_INCLUDE_DIR} ${RGA_LIBRARY}")
message(STATUS "MPP:  ${MPP_INCLUDE_DIR} ${MPP_LIBRARY}")

set(RK3588_CPU_FLAGS)
check_cxx_compiler_flag("-mcpu=cortex-a76.cortex-a55" RK3588_HAS_BIG_LITTLE_MCPU)
if(RK3588_HAS_BIG_LITTLE_MCPU)
    list(APPEND RK3588_CPU_FLAGS -mcpu=cortex-a76.cortex-a55)
else()
    check_cxx_compiler_flag("-mcpu=cortex-a76" RK3588_HAS_A76_MCPU)
    if(RK3588_HAS_A76_MCPU)
        list(APPEND RK3588_CPU_FLAGS -mcpu=cortex-a76)
    endif()
endif()

check_ipo_supported(RESULT RK3588_IPO_SUPPORTED OUTPUT RK3588_IPO_ERROR)

file(GLOB_RECURSE RUNTIME_SOURCES CONFIGURE_DEPENDS ${CMAKE_SOURCE_DIR}/src/*.cpp)
add_executable(RUNTIME ${RUNTIME_SOURCES})
target_include_directories(RUNTIME PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/3rdparty/cpp-httplib
)
target_include_directories(RUNTIME SYSTEM PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${RKNN_INCLUDE_DIR}
    ${RGA_INCLUDE_DIR}
    ${MPP_INCLUDE_DIR}
)

if(DEFINED ENV{CONDA_PREFIX})
    target_include_directories(RUNTIME PRIVATE $ENV{CONDA_PREFIX}/include/opencv5)
endif()

set(OPTIONAL_LIBS)
if(INIH_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${INIH_LIBRARY})
endif()
if(PUGIXML_LIBRARY)
    list(APPEND OPTIONAL_LIBS ${PUGIXML_LIBRARY})
endif()

target_compile_options(RUNTIME PRIVATE
    $<$<CONFIG:Release>:-O3;-DNDEBUG;-ffast-math;-fno-math-errno>
    $<$<CONFIG:Debug>:-O0;-g3>
    ${RK3588_CPU_FLAGS}
    -Wall -Wextra
)
target_compile_definitions(RUNTIME PRIVATE
    GLOG_USE_GLOG_EXPORT
    EASYAIOT_RK3588_STRICT=1
    "RUNTIME_VERSION_STR=\"${RUNTIME_VERSION_STR}\""
)
target_link_libraries(RUNTIME PRIVATE
    ${OpenCV_LIBS}
    ${AVFORMAT_LIBRARY} ${AVCODEC_LIBRARY} ${AVUTIL_LIBRARY}
    ${RKNN_LIBRARY} ${RGA_LIBRARY} ${MPP_LIBRARY}
    CURL::libcurl ${OPTIONAL_LIBS} ${JSONCPP_LIBRARY} ${GLOG_LINK_LIBS}
    pthread dl
)

add_executable(RUNTIME-RK3588-BENCH
    ${CMAKE_SOURCE_DIR}/tools/rknn_benchmark.cpp
    ${CMAKE_SOURCE_DIR}/src/YoloEngine.cpp
    ${CMAKE_SOURCE_DIR}/src/YoloThreadPool.cpp
    ${CMAKE_SOURCE_DIR}/src/rk3588/platform.cpp
)
target_include_directories(RUNTIME-RK3588-BENCH PRIVATE
    ${CMAKE_SOURCE_DIR}/src
)
target_include_directories(RUNTIME-RK3588-BENCH SYSTEM PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${RKNN_INCLUDE_DIR}
    ${RGA_INCLUDE_DIR}
)
target_compile_options(RUNTIME-RK3588-BENCH PRIVATE
    $<$<CONFIG:Release>:-O3;-DNDEBUG;-ffast-math;-fno-math-errno>
    ${RK3588_CPU_FLAGS}
    -Wall -Wextra
)
target_compile_definitions(RUNTIME-RK3588-BENCH PRIVATE GLOG_USE_GLOG_EXPORT)
target_link_libraries(RUNTIME-RK3588-BENCH PRIVATE
    ${OpenCV_LIBS} ${RKNN_LIBRARY} ${RGA_LIBRARY} ${GLOG_LINK_LIBS} pthread dl
)

if(RK3588_IPO_SUPPORTED)
    set_property(TARGET RUNTIME RUNTIME-RK3588-BENCH
                 PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(STATUS "IPO/LTO disabled: ${RK3588_IPO_ERROR}")
endif()

install(TARGETS RUNTIME RUNTIME-RK3588-BENCH DESTINATION bin)

if(BUILD_TESTING)
    add_executable(RUNTIME-RK3588-RING-TEST tests/lockfree_ring_test.cpp)
    target_include_directories(RUNTIME-RK3588-RING-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-RK3588-RING-TEST PRIVATE ${RK3588_CPU_FLAGS} -O2 -Wall -Wextra)
    target_link_libraries(RUNTIME-RK3588-RING-TEST PRIVATE pthread)
    add_test(NAME runtime_rk3588_lockfree_ring COMMAND RUNTIME-RK3588-RING-TEST)
endif()
