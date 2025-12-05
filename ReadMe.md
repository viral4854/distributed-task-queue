# Distributed Task Execution System  
High-Performance Queue • C++17 Multithreaded Workers • Python Producer • RabbitMQ

## Overview
This project implements a high-throughput distributed task execution system using RabbitMQ as the message broker, a Python task producer, and multiple C++17 multithreaded workers. It simulates the architecture of modern distributed compute pipelines—job scheduling, concurrency control, message acknowledgment, and real-time performance.

The system demonstrates how to design scalable, fault-tolerant, and language-agnostic task processing frameworks capable of extremely high throughput.

---

## Architecture

Producer (Python) → RabbitMQ (durable queue) → C++ Multithreaded Workers

+------------------+ +----------------------------+
| Python Producer | -----> | RabbitMQ Queue |
| (JSON tasks) | | (Durable, Persistent) |
+------------------+ +----------------------------+
| | |
v v v
+-----------------------------+
| C++17 Worker Pool (4x) |
| Multithreaded Consumers |
+-----------------------------+


---

## Features

### 🚀 High Throughput
- Python producer publishes **10,000 tasks in ~0.59 seconds**
- C++ worker pool processes **10,000 tasks in 0.0006956 seconds**
- Achieves **~14.37 million tasks per second**

### 🧵 Multithreaded C++ Workers
- Uses `std::thread`, `std::mutex`, `std::chrono`
- Efficient concurrent message handling
- JSON parsing + simulated CPU work per task
- Explicit `ack` for fault-tolerant delivery

### 📦 Reliable Messaging
- Durable queue
- Persistent messages
- Retry counter included in payload
- Crash-safe worker behavior

### 📈 Horizontally Scalable
- Add/remove any number of workers
- No shared-state bottlenecks
- Message ordering preserved (FIFO per queue)

---

## Repository Structure

distributed-task-queue/
│
├── producer.py # Python producer (publishes JSON tasks)
├── worker.py # Python worker (optional variant)
├── worker_sim.cpp # High-performance C++ multithreaded worker
├── README.md # Project documentation
├── requirements.txt # Python dependencies (pika)
└── .gitignore # Build + cache exclusions


---

## How to Run

1. Start RabbitMQ
Download and run RabbitMQ locally:
https://www.rabbitmq.com/docs/download

2. Run the Producer
python3 producer.py

3. Build the C++ Worker
g++ worker_sim.cpp -o worker_sim -lpthread

4. Run Workers

Open multiple terminals and start workers:

./worker_sim