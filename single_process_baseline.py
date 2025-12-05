# single_process_baseline.py
import time
import random


def do_work(value: int):
    # Same fake work as worker.py
    n = int(value)

    def fib(k: int) -> int:
        a, b = 0, 1
        for _ in range(k):
            a, b = b, a + b
        return a

    fib(n)
    time.sleep(0.002)


def run_baseline(num_tasks: int = 10000):
    t0 = time.time()
    for i in range(num_tasks):
        if random.random() < 0.05:
            # mimic occasional failure handling cost
            try:
                raise RuntimeError("simulated failure")
            except RuntimeError:
                pass
        do_work(i % 25)
        if i and i % 1000 == 0:
            print(f"Processed {i} tasks baseline...")
    dt = time.time() - t0
    print(f"Baseline: processed {num_tasks} tasks in {dt:.2f}s")


if __name__ == "__main__":
    run_baseline()
