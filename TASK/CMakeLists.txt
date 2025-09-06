cmake_minimum_required(VERSION 3.16)
project(SmartSurveillanceSystem)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(OpenCV REQUIRED COMPONENTS core videoio highgui imgproc dnn tracking)
find_package(PahoMqttCpp REQUIRED)
find_package(OpenSSL REQUIRED)
find_package(Threads REQUIRED)
find_package(nlohmann_json REQUIRED)

find_path(MINIO_INCLUDE_DIR minio/minio.h)
find_library(MINIO_LIBRARY minio)

include_directories(
        include/
        ${OpenCV_INCLUDE_DIRS}
        ${PahoMqttCpp_INCLUDE_DIRS}
        ${MINIO_INCLUDE_DIR}
)

set(SRC_CORE
        src/core/ConfigurationManager.cpp
        src/core/ServiceLocator.cpp
        src/core/SystemSupervisor.cpp
        src/core/ThreadPool.cpp
)

set(SRC_CAMERAS
        src/cameras/CameraStreamer.cpp
        src/cameras/RTSPCamera.cpp
        src/cameras/USBCamera.cpp
)

set(SRC_PROCESSING
        src/processing/FrameProcessor.cpp
        src/processing/ObjectTracker.cpp
        src/processing/BehaviorAnalyzer.cpp
        src/processing/RegionDetector.cpp
)

set(SRC_AI
        src/ai/InferenceEngine.cpp
        src/ai/ModelManager.cpp
        src/ai/detectors/PersonDetector.cpp
        src/ai/detectors/VehicleDetector.cpp
)

set(SRC_STORAGE
        src/storage/VideoStorage.cpp
        src/storage/LocalStorage.cpp
        src/storage/MinIOClient.cpp
)

set(SRC_ALERT
        src/alert/AlertManager.cpp
        src/alert/MQTTClient.cpp
)

set(SRC_UTILS
        src/utils/Logger.cpp
        src/utils/TimeUtils.cpp
        src/utils/FileUtils.cpp
)

set(ALL_SRC
        src/main.cpp
        ${SRC_CORE}
        ${SRC_CAMERAS}
        ${SRC_PROCESSING}
        ${SRC_AI}
        ${SRC_STORAGE}
        ${SRC_ALERT}
        ${SRC_UTILS}
        include/ai/ModelManager.h
        include/processing/FrameProcessor.h
        src/main.cpp
        src/core/ConfigurationManager.cpp
        src/core/ServiceLocator.cpp
        src/cameras/RTSPCamera.cpp
        src/processing/ObjectTracker.cpp
        src/ai/InferenceEngine.cpp
        src/processing/FrameProcessor.cpp
        src/processing/BehaviorAnalyzer.cpp
        src/alert/AlertManager.cpp
        src/ai/ModelManager.cpp
        src/core/SystemSupervisor.cpp
        src/core/ThreadPool.cpp
)

add_executable(smart_surveillance_system ${ALL_SRC})

target_link_libraries(smart_surveillance_system
        ${OpenCV_LIBS}
        PahoMqttCpp::PahoMqttCpp
        OpenSSL::SSL
        OpenSSL::Crypto
        ${MINIO_LIBRARY}
        Threads::Threads
        nlohmann_json::nlohmann_json
)

install(DIRECTORY config/ DESTINATION ${CMAKE_INSTALL_PREFIX}/config)
install(DIRECTORY models/ DESTINATION ${CMAKE_INSTALL_PREFIX}/models)
install(DIRECTORY resources/ DESTINATION ${CMAKE_INSTALL_PREFIX}/resources)

set_target_properties(smart_surveillance_system PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
        ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

target_compile_options(smart_surveillance_system PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -O3
        -march=native
)

enable_testing()
add_subdirectory(tests)