cmake_minimum_required(VERSION 3.16)
project(RUNTIME_BM1688 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
include(CheckIPOSupported)
include(CTest)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
option(BM1688_HOST_TESTS_ONLY "Only build host-independent ring/config tests" OFF)
set(SOPHON_SDK_ROOT "" CACHE PATH "BM1688 SOPHONSDK root")
set(RUNTIME_VERSION_STR "unknown" CACHE STRING "Runtime version")

if(BM1688_HOST_TESTS_ONLY)
    add_executable(RUNTIME-BM1688-RING-TEST tests/ring_test.cpp)
    target_include_directories(RUNTIME-BM1688-RING-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-BM1688-RING-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    target_link_libraries(RUNTIME-BM1688-RING-TEST PRIVATE pthread)
    add_test(NAME runtime_bm1688_bounded_ring COMMAND RUNTIME-BM1688-RING-TEST)
    return()
endif()

string(TOLOWER "${CMAKE_SYSTEM_PROCESSOR}" EASYAIOT_PROCESSOR)
if(NOT EASYAIOT_PROCESSOR MATCHES "^(aarch64|arm64)$")
    message(FATAL_ERROR
        "RUNTIME-BM1688 only supports BM1688 aarch64 SoC. "
        "Configure on the box or use -DBM1688_HOST_TESTS_ONLY=ON for queue tests.")
endif()

find_package(OpenCV REQUIRED COMPONENTS core imgproc imgcodecs videoio)
find_package(CURL REQUIRED)
find_package(Threads REQUIRED)
find_library(JSONCPP_LIBRARY NAMES jsoncpp REQUIRED)
find_path(JSONCPP_INCLUDE_DIR json/json.h PATH_SUFFIXES jsoncpp REQUIRED)
find_library(AVCODEC_LIBRARY NAMES avcodec REQUIRED)

set(SOPHON_HINTS
    ${SOPHON_SDK_ROOT}
    ${SOPHON_SDK_ROOT}/include
    ${SOPHON_SDK_ROOT}/lib
    /opt/sophon/libsophon-current
    /opt/sophon/sophon-opencv-latest
    /opt/sophon
    /usr /usr/local)

find_path(BMLIB_INCLUDE_DIR bmlib_runtime.h
    HINTS ${SOPHON_HINTS} PATH_SUFFIXES include include/bmlib)
find_path(BMRT_INCLUDE_DIR bmruntime_interface.h
    HINTS ${SOPHON_HINTS} PATH_SUFFIXES include include/bmruntime)
find_path(BMCV_INCLUDE_DIR bmcv_api_ext.h
    HINTS ${SOPHON_HINTS} PATH_SUFFIXES include include/bmcv)
find_library(BMLIB_LIBRARY NAMES bmlib HINTS ${SOPHON_HINTS} PATH_SUFFIXES lib lib64)
find_library(BMRT_LIBRARY NAMES bmrt HINTS ${SOPHON_HINTS} PATH_SUFFIXES lib lib64)
find_library(BMCV_LIBRARY NAMES bmcv HINTS ${SOPHON_HINTS} PATH_SUFFIXES lib lib64)

foreach(required_var
        BMLIB_INCLUDE_DIR BMRT_INCLUDE_DIR BMCV_INCLUDE_DIR
        BMLIB_LIBRARY BMRT_LIBRARY BMCV_LIBRARY)
    if(NOT ${required_var})
        message(FATAL_ERROR
            "Missing BM1688 SOPHONSDK dependency ${required_var}. "
            "Install the BM1688 SDK or set SOPHON_SDK_ROOT.")
    endif()
endforeach()

file(GLOB RUNTIME_SOURCES CONFIGURE_DEPENDS ${CMAKE_SOURCE_DIR}/src/*.cpp)
add_executable(RUNTIME ${RUNTIME_SOURCES})
target_include_directories(RUNTIME PRIVATE
    ${CMAKE_SOURCE_DIR}/src
    ${JSONCPP_INCLUDE_DIR})
target_include_directories(RUNTIME SYSTEM PRIVATE
    ${OpenCV_INCLUDE_DIRS}
    ${BMLIB_INCLUDE_DIR}
    ${BMRT_INCLUDE_DIR}
    ${BMCV_INCLUDE_DIR})
target_compile_options(RUNTIME PRIVATE
    $<$<CONFIG:Release>:-O3;-DNDEBUG;-ffast-math;-fno-math-errno>
    $<$<CONFIG:Debug>:-O0;-g3>
    -mcpu=cortex-a53
    -Wall -Wextra -Wpedantic)
target_compile_definitions(RUNTIME PRIVATE
    EASYAIOT_BM1688_STRICT=1
    "RUNTIME_VERSION_STR=\"${RUNTIME_VERSION_STR}\"")
target_link_libraries(RUNTIME PRIVATE
    ${OpenCV_LIBS}
    ${BMLIB_LIBRARY} ${BMRT_LIBRARY} ${BMCV_LIBRARY}
    ${AVCODEC_LIBRARY} ${JSONCPP_LIBRARY}
    CURL::libcurl Threads::Threads dl)

check_ipo_supported(RESULT BM1688_IPO_SUPPORTED OUTPUT BM1688_IPO_ERROR)
if(BM1688_IPO_SUPPORTED)
    set_property(TARGET RUNTIME PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
else()
    message(STATUS "IPO/LTO disabled: ${BM1688_IPO_ERROR}")
endif()

install(TARGETS RUNTIME DESTINATION bin)

if(BUILD_TESTING)
    add_executable(RUNTIME-BM1688-RING-TEST tests/ring_test.cpp)
    target_include_directories(RUNTIME-BM1688-RING-TEST PRIVATE ${CMAKE_SOURCE_DIR}/src)
    target_compile_options(RUNTIME-BM1688-RING-TEST PRIVATE -O2 -Wall -Wextra -Werror)
    target_link_libraries(RUNTIME-BM1688-RING-TEST PRIVATE pthread)
    add_test(NAME runtime_bm1688_bounded_ring COMMAND RUNTIME-BM1688-RING-TEST)
endif()
