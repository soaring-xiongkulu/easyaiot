#include "Manage.h"

#ifdef _WIN32
#include <windows.h>
#endif

// 全局变量定义
std::atomic<int> s_exit(0);

// 信号处理函数
void procSignal(int s) {
    LOG(INFO) << "receive signal: " << s << ",will exit...";
    s_exit.store(1, std::memory_order_release);
}

#ifdef _WIN32
// Windows平台信号处理
BOOL WINAPI ConsoleHandler(DWORD signal) {
    switch(signal) {
        case CTRL_C_EVENT:
        case CTRL_BREAK_EVENT:
        case CTRL_CLOSE_EVENT:
            procSignal(SIGINT);
            return TRUE;
        default:
            return FALSE;
    }
}

void installSignalCallback() {
    SetConsoleCtrlHandler(ConsoleHandler, TRUE);
    signal(SIGINT, procSignal);
    signal(SIGTERM, procSignal);
    signal(SIGABRT, procSignal);
}

#else
// Linux/Unix平台信号处理
void installSignalCallback() {
    struct sigaction sigIntHandler;
    sigIntHandler.sa_flags = 0;
    sigIntHandler.sa_handler = procSignal;
    sigemptyset(&sigIntHandler.sa_mask);
    sigaction(SIGINT, &sigIntHandler, nullptr);
    sigaction(SIGQUIT, &sigIntHandler, nullptr);
    sigaction(SIGTERM, &sigIntHandler, nullptr);
    sigaction(SIGPIPE, &sigIntHandler, nullptr);
}
#endif

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
