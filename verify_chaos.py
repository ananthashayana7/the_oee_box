import asyncio
import aiohttp
import json
import time

async def run():
    async with aiohttp.ClientSession() as session:
        print("Connecting to Backend WebSocket...")
        try:
            async with session.ws_connect("http://localhost:8000/ws") as ws:
                start_time = time.time()
                while time.time() - start_time < 30:
                    msg = await ws.receive()
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("type") == "update":
                            payload = data.get("data", {})
                            trust = data.get("trust", 1.0)
                            oee = data.get("oee", {})
                            virtual_keys = data.get("virtual_keys", [])

                            print(f"Update: Trust={trust}, OEE={oee.get('oee')}")

                            # Check Virtual Sensor Logic
                            if "state_code" in payload and "state_code (Virtual)" in virtual_keys:
                                print(f"PASS: Virtual State Code detected: {payload['state_code']}")

                            # Check Spike Filtering
                            temp = payload.get("temperature", 0)
                            if temp > 100:
                                print(f"FAIL: Temperature Spike allowed through! ({temp})")
                            elif temp > 0:
                                # In "dirty" mode, simulator injects 500.0 occasionally.
                                # If we see normal temps but trust dips, sanitizer is working.
                                pass

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
