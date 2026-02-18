import asyncio
import logging
from amqtt.broker import Broker

# Simple config for anonymous access
config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '127.0.0.1:1883',
        },
    },
    'sys_interval': 10,
    'auth': {
        'allow-anonymous': True,
        'plugins': ['auth.anonymous'],
    },
    'topic-check': {
        'enabled': False
    }
}

async def start_broker():
    broker = Broker(config)
    await broker.start()
    print("Broker started on 127.0.0.1:1883")
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    # Configure logging to see what's happening
    logging.basicConfig(level=logging.WARNING)
    # Use WARNING level to reduce noise, unless debugging needed

    try:
        asyncio.run(start_broker())
    except KeyboardInterrupt:
        pass
