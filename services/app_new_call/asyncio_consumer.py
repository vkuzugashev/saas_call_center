import asyncio
import aiormq

async def on_message(message):
    """
    on_message doesn't necessarily have to be defined as async.
    Here it is to show that it's possible.
    """
    print(f" [x] Received message {message!r}")
    print(f"Message body is: {message.body!r}")
    print("Before sleep!")
    await asyncio.sleep(5)   # Represents async I/O operations
    print("After sleep!")

async def main():
    # Perform connection
    connection = await aiormq.connect("amqp://guest:guest@localhost/")

    # Creating a channel
    channel = await connection.channel()

    # Declaring queue
    declare_ok = await channel.queue_declare('events')
    consume_ok = await channel.basic_consume(
        declare_ok.queue, on_message, no_ack=True
    )

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()