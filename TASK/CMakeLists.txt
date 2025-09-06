cmake_minimum_required(VERSION 3.16)
project(SmartSurveillanceSystem)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories(
        /usr/include/
        /usr/local/include
        ${CMAKE_SOURCE_DIR}/3rdpart/opencv4/
        ${CMAKE_SOURCE_DIR}/3rdpart/minio-cpp/include/
        ${CMAKE_SOURCE_DIR}/3rdpart/object_detect_Alg/
        ${CMAKE_SOURCE_DIR}/3rdpart/librknn_api/include/
        ${CMAKE_SOURCE_DIR}/3rdpart/mk_media/
        ${CMAKE_SOURCE_DIR}/3rdpart/cpp-httplib/
        ${CMAKE_SOURCE_DIR}/3rdpart/json/single_include/
        ${CMAKE_SOURCE_DIR}/3rdpart/paho/
        /include/
)

link_directories(
        /usr/lib/
        /usr/local/lib/
        /usr/local/lib64/
        /usr/local/openssl/lib
        /data/minio-cpp/build/Debug/
        /data/minio-cpp/build/Debug/vcpkg_installed/arm64-linux/lib/
        ${CMAKE_SOURCE_DIR}/3rdpart/object_detect_Alg/lib_ai/
        ${CMAKE_SOURCE_DIR}/3rdpart/lib/Linux/${LIB_ARCH}/librga.so
        ${CMAKE_SOURCE_DIR}/3rdpart/rga/${DEVICE_NAME}/lib/Linux/${LIB_ARCH}/
        ${CMAKE_SOURCE_DIR}/3rdpart/librknn_api/${LIB_ARCH}/
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
        src/ai/ModelDownloader.cpp
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
        include/SystemSupervisor.h
        include/RTSPCamera.h
        include/BehaviorAnalyzer.h
        include/ServiceLocator.h
        include/ObjectTracker.h
        include/ConfigurationManager.h
        include/ThreadPool.h
        include/AlertManager.h
        include/InferenceEngine.h
        src/cameras/CameraStreamer.cpp
        src/cameras/USBCamera.cpp
        src/ai/ModelDownloader.cpp
        src/storage/VideoStorage.cpp
        src/storage/LocalStorage.cpp
        src/storage/MinIOClient.cpp
        src/alert/MQTTClient.cpp
        src/utils/Logger.cpp
        src/utils/TimeUtils.cpp
        src/ai/detectors/PersonDetector.cpp
        src/ai/detectors/VehicleDetector.cpp
        include/CameraStreamer.h
        include/USBCamera.h
        include/ModelDownloader.h
        include/VideoStorage.h
        include/LocalStorage.h
        include/MinIOClient.h
        include/MQTTClient.h
        include/Logger.h
        include/TimeUtils.h
        include/FileUtils.h
        include/PersonDetector.h
        include/VehicleDetector.h
        src/processing/RegionDetector.cpp
        src/utils/FileUtils.cpp
)

add_executable(TASK ${ALL_SRC})

target_link_libraries(TASK
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

set_target_properties(TASK PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
        ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

target_compile_options(TASK PRIVATE
        -Wall
        -Wextra
        -Wpedantic
        -O3
        -march=native
)