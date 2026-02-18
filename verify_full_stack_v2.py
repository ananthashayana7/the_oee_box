import asyncio
import aiohttp
import json
import time

async def run():
    async with aiohttp.ClientSession() as session:
        # 1. Check Auth (Should fail)
        print("Checking Auth Protection...")
        try:
            async with session.post("http://localhost:8000/command", json={"command": "STOP"}) as resp:
                if resp.status == 401 or resp.status == 403:
                    print("PASS: /command protected (401/403)")
                else:
                    print(f"FAIL: /command returned {resp.status}")
        except Exception as e:
            print(f"Error checking /command: {e}")

        # 2. Login
        print("Logging in...")
        token = None
        try:
            data = {"username": "admin", "password": "admin123"}
            async with session.post("http://localhost:8000/token", data=data) as resp:
                if resp.status == 200:
                    js = await resp.json()
                    token = js["access_token"]
                    print("PASS: Login successful")
                else:
                    print(f"FAIL: Login failed {resp.status}")
        except Exception as e:
            print(f"Error login: {e}")

        # 3. Check Auth (Should succeed)
        if token:
            print("Checking Authorized Command...")
            try:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.post("http://localhost:8000/command", json={"command": "START"}, headers=headers) as resp:
                    if resp.status == 200:
                        print("PASS: Authorized command successful")
                    else:
                        print(f"FAIL: Authorized command returned {resp.status}")
            except Exception as e:
                print(f"Error authorized command: {e}")

        # 4. Wait for AI Shadow Logs
        print("Waiting for AI logs (Shadow Mode)...")
        await asyncio.sleep(40) # Wait for simulator to run and AI to detect low performance

        try:
            async with session.get("http://localhost:8000/audit") as resp:
                logs = await resp.json()
                found_ai = False
                for log in logs:
                    if log["action"] == "AI_SHADOW":
                        found_ai = True
                        print(f"PASS: Found AI Shadow Log: {log['details']}")
                        break
                if not found_ai:
                    print("FAIL: No AI Shadow logs found yet.")
        except Exception as e:
            print(f"Error checking audit logs: {e}")

if __name__ == "__main__":
    asyncio.run(run())
