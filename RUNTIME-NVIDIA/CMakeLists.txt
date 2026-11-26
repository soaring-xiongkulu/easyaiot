cmake_minimum_required(VERSION 3.18)
project(RUNTIME_NVIDIA LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
include(CheckIPOSupported)
include(CTest)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

option(NVIDIA_HOST_TESTS_ONLY "Only build host-independent queue/config tests" OFF)
set(TENSORRT_ROOT "" CACHE PATH "TensorRT installation root")
set(RUNTIME_VERSION_STR "unknown" CACHE STRING "Runtime version")

if(NVIDIA_HOST_TESTS_ONLY)
    add_executable(RUNTIME-NVIDIA-RING-TEST tests/ring_test.cpp)
    target_include_directories(RUNTIME-NVIDIA-RING-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-NVIDIA-RING-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    target_link_libraries(RUNTIME-NVIDIA-RING-TEST PRIVATE pthread)
    add_test(NAME runtime_nvidia_bounded_ring COMMAND RUNTIME-NVIDIA-RING-TEST)
    add_executable(RUNTIME-NVIDIA-CONFIG-TEST tests/config_test.cpp src/Config.cpp)
    target_include_directories(RUNTIME-NVIDIA-CONFIG-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-NVIDIA-CONFIG-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    add_test(NAME runtime_nvidia_strict_config COMMAND RUNTIME-NVIDIA-CONFIG-TEST)
    return()
endif()

enable_language(CUDA)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "Linux")
    message(FATAL_ERROR "RUNTIME-NVIDIA only supports Linux NVIDIA edge boxes")
endif()

find_package(CUDAToolkit REQUIRED)
find_package(CURL REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(Threads REQUIRED)
pkg_check_modules(AVFORMAT REQUIRED IMPORTED_TARGET libavformat)
pkg_check_modules(AVCODEC REQUIRED IMPORTED_TARGET libavcodec)
pkg_check_modules(AVUTIL REQUIRED IMPORTED_TARGET libavutil)
find_library(JSONCPP_LIBRARY NAMES jsoncpp REQUIRED)
find_path(JSONCPP_INCLUDE_DIR json/json.h PATH_SUFFIXES jsoncpp REQUIRED)

set(TENSORRT_HINTS
    ${TENSORRT_ROOT}
    ${TENSORRT_ROOT}/include
    ${TENSORRT_ROOT}/lib
    ${TENSORRT_ROOT}/lib64
    /usr /usr/local /usr/lib/aarch64-linux-gnu /usr/lib/x86_64-linux-gnu)
find_path(TENSORRT_INCLUDE_DIR NvInfer.h HINTS ${TENSORRT_HINTS} PATH_SUFFIXES include)
find_library(NVINFER_LIBRARY NAMES nvinfer HINTS ${TENSORRT_HINTS} PATH_SUFFIXES lib lib64)
if(NOT TENSORRT_INCLUDE_DIR OR NOT NVINFER_LIBRARY)
    message(FATAL_ERROR "TensorRT headers/library not found; install TensorRT or set TENSORRT_ROOT")
endif()

if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64)$")
        set(CMAKE_CUDA_ARCHITECTURES 72 87)
    else()
        set(CMAKE_CUDA_ARCHITECTURES 75 86 89)
    endif()
endif()

set(RUNTIME_SOURCES
    src/Config.cpp
    src/CudaPreprocess.cu
    src/EventBus.cpp
    src/NvDecoder.cpp
    src/Pipeline.cpp
    src/TensorRtEngine.cpp
    src/main.cpp)
add_executable(RUNTIME ${RUNTIME_SOURCES})
target_include_directories(RUNTIME PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${JSONCPP_INCLUDE_DIR}
    ${TENSORRT_INCLUDE_DIR})
target_compile_options(RUNTIME PRIVATE
    $<$<COMPILE_LANGUAGE:CXX>:-Wall;-Wextra;-Wpedantic>
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CONFIG:Release>>:-O3;-DNDEBUG;-ffast-math;-fno-math-errno>
    $<$<AND:$<COMPILE_LANGUAGE:CUDA>,$<CONFIG:Release>>:-O3;--use_fast_math>)
target_compile_definitions(RUNTIME PRIVATE
    EASYAIOT_NVIDIA_STRICT=1
    "RUNTIME_VERSION_STR=\"${RUNTIME_VERSION_STR}\"")
set_target_properties(RUNTIME PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
target_link_libraries(RUNTIME PRIVATE
    CUDA::cudart
    ${NVINFER_LIBRARY}
    PkgConfig::AVFORMAT PkgConfig::AVCODEC PkgConfig::AVUTIL
    ${JSONCPP_LIBRARY}
    CURL::libcurl Threads::Threads dl)

check_ipo_supported(RESULT NVIDIA_IPO_SUPPORTED OUTPUT NVIDIA_IPO_ERROR)
if(NVIDIA_IPO_SUPPORTED)
    set_property(TARGET RUNTIME PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(STATUS "IPO/LTO disabled: ${NVIDIA_IPO_ERROR}")
endif()

install(TARGETS RUNTIME DESTINATION bin)

if(BUILD_TESTING)
    add_executable(RUNTIME-NVIDIA-RING-TEST tests/ring_test.cpp)
    target_include_directories(RUNTIME-NVIDIA-RING-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-NVIDIA-RING-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    target_link_libraries(RUNTIME-NVIDIA-RING-TEST PRIVATE pthread)
    add_test(NAME runtime_nvidia_bounded_ring COMMAND RUNTIME-NVIDIA-RING-TEST)
    add_executable(RUNTIME-NVIDIA-CONFIG-TEST tests/config_test.cpp src/Config.cpp)
    target_include_directories(RUNTIME-NVIDIA-CONFIG-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-NVIDIA-CONFIG-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    add_test(NAME runtime_nvidia_strict_config COMMAND RUNTIME-NVIDIA-CONFIG-TEST)
endif()
