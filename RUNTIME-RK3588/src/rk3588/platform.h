#ifndef EASYAIOT_RK3588_PLATFORM_H
#define EASYAIOT_RK3588_PLATFORM_H

#include <string>
#include <vector>

namespace runtime::rk3588 {

struct PlatformReport {
    bool aarch64{false};
    bool rk3588{false};
    bool rknpuDevice{false};
    bool rgaDevice{false};
    bool mppDevice{false};
    bool drmRenderDevice{false};
    std::string machine;
    std::string compatible;
    std::vector<std::string> errors;

    bool ready() const {
        return aarch64 && rk3588 && rknpuDevice && rgaDevice && mppDevice && drmRenderDevice;
    }
    std::string summary() const;
};

PlatformReport inspectPlatform();
bool requirePlatform();

}  // namespace runtime::rk3588

#endif
