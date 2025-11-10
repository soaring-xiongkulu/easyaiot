// @author 翱翔的雄库鲁
// @email andywebjava@163.com
// @wechat EasyAIoT2025

#include "Manage.h"

Server::Server(const Config &conf) : _local(conf) {
}

Server::~Server() {
    stop();
}

void Server::waitForShutdown() {
    if (!_isRun.load(std::memory_order_acquire)) {
        return;
    }
    installSignalCallback();
    while (_isRun.load(std::memory_order_acquire)) {
        if (s_exit.load(std::memory_order_acquire)) {
            break;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

bool Server::start() {
    if (_isRun.load(std::memory_order_acquire)) {
        return true;
    }
    try {
        _detectHandle = std::make_unique<Detech>(_local);
        int ret = _detectHandle->start();
        if (ret != 0) {
            LOG(ERROR) << "CManage start failed.errcode:" << ret;
            _detectHandle.reset();
            return false;
        }
    } catch (const std::exception &e) {
        LOG(ERROR) << "CManage start exception: " << e.what();
        return false;
    }
    _isRun.store(true, std::memory_order_release);
    return true;
}

void Server::stop() {
    _isRun.store(false, std::memory_order_release);
    if (_detectHandle) {
        _detectHandle.reset();
    }
    LOG(WARNING) << "ALL RELEASE success.";
}

bool Server::isRun() const {
    return _isRun.load(std::memory_order_acquire);
}

bool Server::isTerminal() const {
    return _isTerminal.load(std::memory_order_acquire);
}
