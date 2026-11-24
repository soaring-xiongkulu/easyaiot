#include "rk3588/platform.h"

#include <fstream>
#include <glog/logging.h>
#include <initializer_list>
#include <sstream>
#include <sys/utsname.h>
#include <unistd.h>

namespace runtime::rk3588 {
namespace {

std::string readBinaryText(const char* path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) return {};
    std::ostringstream out;
    out << input.rdbuf();
    std::string value = out.str();
    for (char& c : value) {
        if (c == '\0') c = ',';
    }
    return value;
}

bool exists(const char* path) { return ::access(path, F_OK) == 0; }

bool anyExists(std::initializer_list<const char*> paths) {
    for (const char* path : paths) {
        if (exists(path)) return true;
    }
    return false;
}

}  // namespace

std::string PlatformReport::summary() const {
    std::ostringstream out;
    out << "machine=" << machine
        << " compatible=" << compatible
        << " rknpu=" << (rknpuDevice ? "ok" : "missing")
        << " rga=" << (rgaDevice ? "ok" : "missing")
        << " mpp=" << (mppDevice ? "ok" : "missing")
        << " drm=" << (drmRenderDevice ? "ok" : "missing");
    return out.str();
}

PlatformReport inspectPlatform() {
    PlatformReport report;
    struct utsname info {};
    if (::uname(&info) == 0) report.machine = info.machine;
    report.aarch64 = report.machine == "aarch64" || report.machine == "arm64";
    report.compatible = readBinaryText("/proc/device-tree/compatible");
    if (report.compatible.empty()) {
        report.compatible = readBinaryText("/sys/firmware/devicetree/base/compatible");
    }
    report.rk3588 = report.compatible.find("rockchip,rk3588") != std::string::npos;
    report.rknpuDevice = anyExists({"/dev/rknpu", "/dev/rknpu0"});
    report.rgaDevice = anyExists({"/dev/rga", "/dev/rga2"});
    report.mppDevice = anyExists({"/dev/mpp_service", "/dev/vpu_service", "/dev/hevc_service"});
    report.drmRenderDevice = anyExists({"/dev/dri/renderD128", "/dev/dri/card0"});

    if (!report.aarch64) report.errors.emplace_back("CPU 架构不是 aarch64");
    if (!report.rk3588) report.errors.emplace_back("设备树未声明 rockchip,rk3588/rk3588s");
    if (!report.rknpuDevice) report.errors.emplace_back("缺少 /dev/rknpu NPU 驱动节点");
    if (!report.rgaDevice) report.errors.emplace_back("缺少 /dev/rga RGA 驱动节点");
    if (!report.mppDevice) report.errors.emplace_back("缺少 MPP/VPU 驱动节点");
    if (!report.drmRenderDevice) report.errors.emplace_back("缺少 DRM render 节点");
    return report;
}

bool requirePlatform() {
    const PlatformReport report = inspectPlatform();
    if (report.ready()) {
        LOG(INFO) << "[RK3588] 平台自检通过 " << report.summary();
        return true;
    }
    LOG(ERROR) << "[RK3588] 平台自检失败，拒绝启动: " << report.summary();
    for (const auto& error : report.errors) LOG(ERROR) << "[RK3588] - " << error;
    return false;
}

}  // namespace runtime::rk3588
