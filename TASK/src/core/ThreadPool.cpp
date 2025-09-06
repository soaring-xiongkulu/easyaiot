#include "ThreadPool.h"
#include <iostream>

ThreadPool::ThreadPool(size_t threads)
    : stop(false)
{
    for(size_t i = 0; i < threads; ++i)
    {
        workers.emplace_back([this]
        {
            for(;;)
            {
                std::function<void()> task;
                {
                    std::unique_lock<std::mutex> lock(this->queue_mutex);
                    this->condition.wait(lock, [this]
                    {
                        return this->stop || !this->tasks.empty();
                    });
                    if(this->stop && this->tasks.empty())
                        return;
                    task = std::move(this->tasks.front());
                    this->tasks.pop();
                }
                task();
            }
        });
    }
}

ThreadPool::~ThreadPool()
{
    {
        std::unique_lock<std::exclusive_mutex> lock(queue_mutex);
        stop = true;
    }
    condition.notify_all();
    for(std::thread &worker : workers)
        worker.join();
}

template<class F, class... Args>
auto ThreadPool::enqueue(F&& f, Args&&... args) -> std::future<decltype(f(args...))>
{
    using return_type = decltype(f(args...));

    auto task = std::make_shared<std::packaged_task<return_type()>>(
        std::bind(std::forward<F>(f), std::forward<Args>(args)...)
    );

    std::future<return_type> res = task->get_future();
    {
        std::unique_lock<std::exclusive_mutex> lock(queue_mutex);

        if(stop)
            throw std::runtime_error("enqueue on stopped ThreadPool");

        tasks.emplace([task](){ (*task)(); });
    }
    condition.notify_one();
    return res;
}

size_t ThreadPool::size() const
{
    std::unique_lock<std::exclusive_mutex> lock(queue_mutex);
    return workers.size();
}

size_t ThreadPool::idleSize() const
{
    std::unique_lock<std::exclusive_mutex> lock(queue_mutex);
    return tasks.size();
}

void ThreadPool::waitForCompletion()
{
    std::unique_lock<std::exclusive_mutex> lock(queue_mutex);
    completion_condition.wait(lock, [this]
    {
        return tasks.empty();
    });
}