#include <iostream>
#include <vector>
#include <thread>
#include <queue>
#include <mutex>
#include <chrono>
#include <atomic>
#include <random>

struct Task {
    int id;
    int value;
};

// Simple thread-safe queue
class TaskQueue {
public:
    void push(const Task& t) {
        std::lock_guard<std::mutex> lock(mtx_);
        q_.push(t);
    }

    bool pop(Task& out) {
        std::lock_guard<std::mutex> lock(mtx_);
        if (q_.empty()) return false;
        out = q_.front();
        q_.pop();
        return true;
    }

    bool empty() const {
        // harmless race, only used for termination check
        return q_.empty();
    }

private:
    mutable std::mutex mtx_;
    std::queue<Task> q_;
};

// Fake “work” – some CPU math so threads actually do something
int do_work(int value) {
    int x = value;
    for (int i = 0; i < 1000; ++i) {
        x = (x * 1664525 + 1013904223) & 0x7fffffff;
    }
    return x;
}

int main() {
    const int NUM_TASKS = 10000;
    const int NUM_WORKERS = 4;

    TaskQueue queue;
    std::atomic<int> processed{0};

    // Pre-load tasks
    for (int i = 0; i < NUM_TASKS; ++i) {
        queue.push(Task{i, i % 25});
    }

    auto start = std::chrono::high_resolution_clock::now();

    // Worker threads
    std::vector<std::thread> workers;
    for (int i = 0; i < NUM_WORKERS; ++i) {
        workers.emplace_back([&queue, &processed, i]() {
            Task t;
            while (true) {
                if (!queue.pop(t)) {
                    // queue drained
                    return;
                }
                int result = do_work(t.value);
                (void)result; // ignored, we just simulate CPU work
                ++processed;
            }
        });
    }

    for (auto &th : workers) {
        th.join();
    }

    auto end = std::chrono::high_resolution_clock::now();
    double seconds = std::chrono::duration<double>(end - start).count();

    std::cout << "Processed " << processed.load() << " tasks with "
              << NUM_WORKERS << " C++ workers in "
              << seconds << "s ("
              << (processed.load() / seconds) << " tasks/sec)" << std::endl;

    return 0;
}
