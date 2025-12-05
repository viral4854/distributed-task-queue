# producer.py
import argparse
import json
import time

import pika

from config import RABBITMQ_HOST, TASK_QUEUE

def get_connection():
    params = pika.ConnectionParameters(host=RABBITMQ_HOST)
    return pika.BlockingConnection(params)

def publish_tasks(num_tasks: int):
    connection = get_connection()
    channel = connection.channel()

    # durable queue so messages survive broker restart
    channel.queue_declare(queue=TASK_QUEUE, durable=True)

    t0 = time.time()
    for task_id in range(num_tasks):
        payload = {
            "id": task_id,
            "value": task_id % 25,  # arbitrary payload
            "retry_count": 0,
        }
        body = json.dumps(payload)

        channel.basic_publish(
            exchange="",
            routing_key=TASK_QUEUE,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2  # make message persistent
            ),
        )

        if task_id and task_id % 1000 == 0:
            print(f"Enqueued {task_id} tasks...")

    connection.close()
    dt = time.time() - t0
    print(f"Enqueued {num_tasks} tasks in {dt:.2f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-tasks", type=int, default=10000)
    args = parser.parse_args()

    publish_tasks(args.num_tasks)
