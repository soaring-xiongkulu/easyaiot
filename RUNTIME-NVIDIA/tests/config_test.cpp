#include "Config.h"

#include <chrono>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

class TempDirectory {
public:
    TempDirectory() {
        const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
        path = std::filesystem::temp_directory_path() /
               ("easyaiot-runtime-nvidia-config-" + std::to_string(stamp));
        std::filesystem::create_directories(path);
    }
    ~TempDirectory() { std::filesystem::remove_all(path); }

    std::filesystem::path path;
};

void writeText(const std::filesystem::path& path, const std::string& content) {
    std::ofstream output(path, std::ios::binary);
    if (!output) throw std::runtime_error("cannot create test fixture");
    output << content;
}

std::string configText(const std::filesystem::path& model,
                       const std::filesystem::path& classes,
                       const std::string& nvidiaOverride = {}) {
    return "[video]\n"
           "rtsp_url=rtsp://127.0.0.1/live\n"
           "[ai]\n"
           "model_path=" + model.string() + "\n"
           "classes_path=" + classes.string() + "\n"
           "[nvidia]\n"
           "zero_copy=true\n"
           "preallocate=true\n"
           "require_nvdec=true\n"
           "require_nvenc=false\n" + nvidiaOverride +
           "[features]\n"
           "enable_rtmp=false\n"
           "[video_task]\n"
           "task_type=realtime\n";
}

template <typename Callback>
void mustReject(Callback&& callback, const std::string& expected) {
    bool rejected = false;
    try {
        callback();
    } catch (const std::runtime_error& error) {
        rejected = true;
        require(std::string(error.what()).find(expected) != std::string::npos,
                "configuration failed for an unexpected reason");
    }
    require(rejected, "configuration should have been rejected");
}

}  // namespace

int main() {
    TempDirectory temporary;
    const auto engine = temporary.path / "model.engine";
    const auto onnx = temporary.path / "model.onnx";
    const auto classes = temporary.path / "coco.names";
    const auto config = temporary.path / "task.ini";
    writeText(engine, "fake-engine");
    writeText(onnx, "fake-onnx");
    writeText(classes, "person\n");

    writeText(config, configText(engine, classes));
    const auto parsed = easyaiot::nvidia::ConfigParser::load(config.string());
    require(parsed.models.size() == 1, "expected one TensorRT model");
    require(parsed.models.front().path == engine.string(), "engine path mismatch");
    require(parsed.zeroCopy && parsed.preallocate && parsed.requireNvdec,
            "strict NVIDIA flags were not loaded");
    require(!parsed.requireNvenc && !parsed.enableRtmp,
            "unsupported NVENC output should be disabled");

    writeText(config, configText(onnx, classes));
    mustReject(
        [&] { easyaiot::nvidia::ConfigParser::load(config.string()); },
        ".engine/.plan only");

    writeText(config, configText(engine, classes, "zero_copy=false\n"));
    mustReject(
        [&] { easyaiot::nvidia::ConfigParser::load(config.string()); },
        "strict mode");

    writeText(config, configText(engine, classes, "require_nvenc=true\n"));
    mustReject(
        [&] { easyaiot::nvidia::ConfigParser::load(config.string()); },
        "NVENC output is not enabled");
    return 0;
}
