cmake_minimum_required(VERSION 3.5)

PROJECT (TASK)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17 -pthread ")

set(CMAKE_BUILD_TYPE DEBUG)
SET(CMAKE_CXX_FLAGS_DEBUG "$ENV{CXXFLAGS} -O0 -Wall -g2 -ggdb")
SET(CMAKE_CXX_FLAGS_RELEASE "$ENV{CXXFLAGS} -O3 -Wall")

set(ARCH_X86_64 "x86_64")
set(ARCH_AARCH64 "aarch64")

find_package(OpenCV REQUIRED)
message(STATUS "OpenCV: ${OpenCV_INCLUDE_DIRS}")
message(STATUS "${OpenCV_VERSION}")

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
        ${CMAKE_SOURCE_DIR}/3rdpart/cpp-httplib/
)

file (GLOB Src_SOURCES ${CMAKE_SOURCE_DIR}/src/*.cpp)

add_executable(${PROJECT_NAME} ${Src_SOURCES})

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
