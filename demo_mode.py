import subprocess
import time
import signal
import sys
import os

processes = []

def start_process(command, name):
    print(f"Starting {name}...")
    p = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
    processes.append(p)
    return p

def cleanup(signum, frame):
    print("\nStopping Demo Mode...")
    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# 1. Start Infrastructure
start_process("amqtt -c amqtt_config.yaml -d > amqtt.log 2>&1", "MQTT Broker")
time.sleep(2)
start_process("uvicorn backend.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1", "Backend")
start_process("cd frontend && npm run dev > frontend.log 2>&1", "Frontend")
time.sleep(5)

# 2. Start Simulators (Chaos Orchestration)
print("Launching Machines...")

# Machine 1: Clean (The Benchmark)
start_process("python simulator.py --id machine_1 --mode clean > sim_m1.log 2>&1", "Machine 1 (Clean)")

# Machine 2: Clean
start_process("python simulator.py --id machine_2 --mode clean > sim_m2.log 2>&1", "Machine 2 (Clean)")

# Machine 3: Dumb (Testing Virtual Sensors)
start_process("python simulator.py --id machine_3 --mode dumb > sim_m3.log 2>&1", "Machine 3 (Dumb/Virtual)")

# Machine 4: Dirty (Testing Trust Scores)
start_process("python simulator.py --id machine_4 --mode dirty > sim_m4.log 2>&1", "Machine 4 (Dirty/Chaos)")

# Machine 5: Faulty (Testing Alerts)
start_process("python simulator.py --id machine_5 --mode faulty > sim_m5.log 2>&1", "Machine 5 (Faulty)")

print("\n--- DEMO MODE ACTIVE ---")
print("Access Dashboard at http://localhost:5173")
print("Press Ctrl+C to stop.")

while True:
    time.sleep(1)
