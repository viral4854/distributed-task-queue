import json
import pika
import time

MAIN_QUEUE = "task_queue"
DLQ_QUEUE = "task_queue_dlq"

MAX_RETRIES = 3

def process_task(task: dict) -> bool:
    """
    Simulate transient failures.
    - Fail once for some tasks
    - Succeed on retry
    - Only a few go to DLQ
    """
    task_id = task["id"]
    retry_count = task.get("retry_count", 0)

    # 1 out of 10 tasks fail on first attempt only
    if task_id % 10 == 0 and retry_count < 1:
        return False

    # 1 out of 50 tasks fail twice
    if task_id % 50 == 0 and retry_count < 2:
        return False

    return True


def callback(ch, method, properties, body: bytes):
    task = json.loads(body.decode("utf-8"))
    retry_count = int(task.get("retry_count", 0))

    try:
        ok = process_task(task)
        if ok:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        raise Exception("simulated failure")

    except Exception:
        retry_count += 1
        task["retry_count"] = retry_count

        if retry_count >= MAX_RETRIES:
            # publish to DLQ, then ack original
            ch.basic_publish(
                exchange="",
                routing_key=DLQ_QUEUE,
                body=json.dumps(task).encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type="application/json",
                ),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"DLQ -> id={task.get('id')} retries={retry_count}")
        else:
            # reject without requeue; RabbitMQ routes it to retry queue via DLX
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            print(f"RETRY -> id={task.get('id')} attempt={retry_count}")

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=MAIN_QUEUE, on_message_callback=callback)

    print("Worker (retry+DLQ) started. Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
