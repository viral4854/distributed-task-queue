# worker.py
import json
import time
import random

import pika

from config import (
    RABBITMQ_HOST,
    TASK_QUEUE,
    DEAD_LETTER_QUEUE,
    RETRY_LIMIT,
)


def get_connection():
    params = pika.ConnectionParameters(host=RABBITMQ_HOST)
    return pika.BlockingConnection(params)


def do_work(payload: dict):
    """
    Simulated CPU work. Replace with real logic later.
    Here we compute a dumb fibonacci and sometimes raise an error
    to exercise retry logic.
    """
    n = int(payload["value"])

    # ~5% failure rate to test retries
    if random.random() < 0.05:
        raise RuntimeError("Simulated failure")

    def fib(k: int) -> int:
        a, b = 0, 1
        for _ in range(k):
            a, b = b, a + b
        return a

    fib(n)  # just burn some CPU
    time.sleep(0.002)  # tiny delay to simulate work


def main():
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue=TASK_QUEUE, durable=True)
    channel.queue_declare(queue=DEAD_LETTER_QUEUE, durable=True)

    # Don't send more than one unacked message to a worker at a time
    channel.basic_qos(prefetch_count=1)

    print("Worker started. Waiting for tasks...")

    def on_message(ch, method, properties, body: bytes):
        payload = json.loads(body.decode("utf-8"))
        task_id = payload["id"]
        retry_count = payload.get("retry_count", 0)

        start = time.time()
        try:
            do_work(payload)
            elapsed = (time.time() - start) * 1000
            print(f"[OK ] Task {task_id} done in {elapsed:.2f} ms (retry={retry_count})")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"[ERR] Task {task_id} failed: {e} (retry={retry_count})")
            ch.basic_ack(delivery_tag=method.delivery_tag)

            retry_count += 1
            payload["retry_count"] = retry_count

            if retry_count <= RETRY_LIMIT:
                # republish to main queue
                ch.basic_publish(
                    exchange="",
                    routing_key=TASK_QUEUE,
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
                print(f" -> requeued task {task_id} (retry={retry_count})")
            else:
                # send to dead-letter queue
                ch.basic_publish(
                    exchange="",
                    routing_key=DEAD_LETTER_QUEUE,
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
                print(f" -> sent task {task_id} to dead-letter queue")

    channel.basic_consume(queue=TASK_QUEUE, on_message_callback=on_message)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping worker...")
        channel.stop_consuming()
        connection.close()


if __name__ == "__main__":
    main()
