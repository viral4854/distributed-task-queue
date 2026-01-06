import pika

MAIN_QUEUE = "task_queue"
RETRY_QUEUE = "task_queue_retry"
DLQ_QUEUE = "task_queue_dlq"
DLX_EXCHANGE = "dlx"

# retry delay in ms
RETRY_DELAY_MS = 5000

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    # Dead-letter exchange (routes rejected messages from main -> retry queue)
    channel.exchange_declare(exchange=DLX_EXCHANGE, exchange_type="direct", durable=True)

    # DLQ: terminal queue for permanently failed tasks
    channel.queue_declare(queue=DLQ_QUEUE, durable=True)

    # Retry queue: holds messages for RETRY_DELAY_MS, then routes back to main queue
    channel.queue_declare(
        queue=RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": MAIN_QUEUE,
        },
    )

    # Main queue: on reject(requeue=False) -> DLX -> retry queue
    channel.queue_declare(
        queue=MAIN_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": DLX_EXCHANGE,
            "x-dead-letter-routing-key": RETRY_QUEUE,
        },
    )

    # Bind DLX routing key to retry queue
    channel.queue_bind(exchange=DLX_EXCHANGE, queue=RETRY_QUEUE, routing_key=RETRY_QUEUE)

    print("OK: queues ready ->", MAIN_QUEUE, RETRY_QUEUE, DLQ_QUEUE)
    connection.close()

if __name__ == "__main__":
    main()
