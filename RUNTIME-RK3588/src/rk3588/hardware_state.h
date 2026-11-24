#ifndef EASYAIOT_RK3588_HARDWARE_STATE_H
#define EASYAIOT_RK3588_HARDWARE_STATE_H

#include <string>

namespace runtime::rk3588 {

struct MppDecodeState {
    bool active{false};
    std::string endpoint{"none"};
};

inline void reset(MppDecodeState& state) {
    state.active = false;
    state.endpoint = "none";
}

}  // namespace runtime::rk3588

#endif
