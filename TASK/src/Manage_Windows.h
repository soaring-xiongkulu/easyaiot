#ifndef MANAGE_H_
#define MANAGE_H_

#include <atomic>
#include <memory>
#include <thread>
#include <functional>
#include <glog/logging.h>
#include <chrono>
#include <Detech.h>
#include <iostream>

#include "Config.h"

std::atomic<int> s_exit(0);

#ifdef _WIN32
// Windows平台信号处理
#include <windows.h>
#include <csignal>

void procSignal(int s) {
    LOG(INFO) << "receive signal: " << s << ",will exit...";
    s_exit.store(1, std::memory_order_release);
}

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
#include <csignal>

void procSignal(int s) {
    LOG(INFO) << "receive signal: " << s << ",will exit...";
    s_exit.store(1, std::memory_order_release);
}

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

class Server {
public:
    explicit Server(const Config &conf);
    ~Server();
    void waitForShutdown();
    bool start();
    void stop();
    bool isRun() const;
    bool isTerminal() const;

private:
    std::atomic<bool> _isRun{false};
    std::atomic<bool> _isTerminal{false};
    Config _local;
    std::unique_ptr<Detech> _detectHandle;
};
#endif  // MANAGE_H_

#define MANAGE_H_

#include <atomic>
#include <memory>
#include <thread>
#include <functional>
#include <glog/logging.h>
#include <chrono>
#include <Detech.h>
#include <iostream>

#include "Config.h"

std::atomic<int> s_exit(0);

#ifdef _WIN32
// Windows平台信号处理
#include <windows.h>
#include <csignal>

void procSignal(int s) {
    LOG(INFO) << "receive signal: " << s << ",will exit...";
    s_exit.store(1, std::memory_order_release);
}

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
#include <csignal>

void procSignal(int s) {
    LOG(INFO) << "receive signal: " << s << ",will exit...";
    s_exit.store(1, std::memory_order_release);
}

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

class Server {
public:
    explicit Server(const Config &conf);
    ~Server();
    void waitForShutdown();
    bool start();
    void stop();
    bool isRun() const;
    bool isTerminal() const;

private:
    std::atomic<bool> _isRun{false};
    std::atomic<bool> _isTerminal{false};
    Config _local;
    std::unique_ptr<Detech> _detectHandle;
};
#endif  // MANAGE_H_
