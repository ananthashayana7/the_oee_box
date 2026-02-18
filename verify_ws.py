import asyncio
import websockets
import json
import time

async def verify():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            # Wait for a few messages
            for _ in range(3):
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received update. Schema keys: {data.get('schema', {}).keys()}")
                print(f"OEE: {data.get('oee')}")
    except Exception as e:
        print(f"WS Error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
