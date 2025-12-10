#ifndef MANAGE_H_
#define MANAGE_H_

#include <atomic>
#include <memory>
#include <thread>
#include <functional>
#include <glog/logging.h>
#include <csignal>
#include <chrono>
#include <Detech.h>
#include <iostream>

#include "Config.h"

// 声明全局变量和函数（定义在Manage.cpp中）
extern std::atomic<int> s_exit;
void procSignal(int s);
void installSignalCallback();

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