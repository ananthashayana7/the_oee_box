from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import asyncio
import json
from collections import deque
from contextlib import asynccontextmanager
from backend.mqtt_client import mqtt_service
from backend.rl_agent import RLAgent
from backend.command_gatekeeper import CommandGatekeeper
from backend.copilot import ChatAgent
from backend.database import db_manager
from backend.alert_engine import alert_engine
from backend.auth import authenticate_user, create_access_token, get_current_active_user, get_authorized_user, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models import Token, User
from backend.models_config import MachineConfig
from backend.machine_manager import machine_manager
from backend.reporting import generate_plant_report
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Global State
gatekeeper = CommandGatekeeper()
chat_agent = ChatAgent()
rl_agent = None
connected_websockets = set()

class Command(BaseModel):
    command: str
    target: str = "factory/line1/machine1/command"
    signature: str | None = None

class ChatRequest(BaseModel):
    query: str
    machine_id: str | None = None

async def broadcast(message):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            connected_websockets.discard(ws)

def get_machine_id_from_topic(topic):
    # Topic format: factory/line1/{machine_id}/data
    parts = topic.split('/')
    if len(parts) >= 4 and parts[3] == "data":
        return parts[2]
    return "unknown_machine"

async def handle_mqtt_message(topic, payload):
    try:
        # Only process data topic for OEE
        if "/data" not in topic:
            return

        machine_id = get_machine_id_from_topic(topic)
        machine = machine_manager.get_machine(machine_id)

        raw_data = json.loads(payload)

        # Sanitization (The Bouncer)
        data, trust_scores, explanations = machine.sanitizer.process(raw_data)
        machine.current_data = data

        # Persist to DB (Sanitized)
        timestamp = data.get("timestamp", 0)
        for k, v in data.items():
            if k != "timestamp":
                await db_manager.insert_telemetry(timestamp, machine_id, k, v)

        # Alerts
        await alert_engine.process(data)
        alerts = await db_manager.get_active_alerts()

        # Virtual Sensors (The Adapter)
        v_data, v_trust, v_keys = machine.virtual_factory.process(data, trust_scores)
        machine.virtual_keys = v_keys

        # Process Schema
        machine.schema_engine.process(v_data)
        machine.schema = machine.schema_engine.get_schema()

        # Calculate OEE
        oee_result = machine.oee_calculator.update(machine.schema, v_data)
        if oee_result:
            machine.latest_oee = oee_result

        # Calculate Global Trust Score
        global_trust = sum(v_trust.values()) / len(v_trust) if v_trust else 1.0
        machine.latest_oee["trust"] = global_trust

        # Broadcast
        msg = {
            "type": "update",
            "machine_id": machine_id,
            "data": v_data,
            "schema": machine.schema,
            "oee": machine.latest_oee,
            "alerts": alerts,
            "trust": round(global_trust, 2),
            "virtual_keys": v_keys,
            "explanations": explanations
        }
        await broadcast(msg)
    except json.JSONDecodeError:
        pass
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rl_agent
    # Startup
    logger.info("Connecting to Database...")
    await db_manager.connect()

    logger.info("Starting MQTT Service...")
    try:
        loop = asyncio.get_running_loop()
        mqtt_service.message_callback = handle_mqtt_message
        mqtt_service.start(loop=loop)

        # Start RL Agent (For Demo, attach to machine1)
        logger.info("Starting RL Agent...")
        # Note: RL Agent currently hardcoded to fetch latest_oee global.
        # We need to adapt it if we want multi-machine RL.
        # For now, let's bind it to machine_1
        def get_machine1_oee():
            return machine_manager.get_machine("machine_1").latest_oee

        rl_agent = RLAgent(get_machine1_oee, mode="shadow")
        asyncio.create_task(rl_agent.start())

        # Start Data Retention Task
        async def data_retention_loop():
            while True:
                await asyncio.sleep(3600) # Run every hour
                await db_manager.cleanup_old_data(days=30)

        asyncio.create_task(data_retention_loop())

    except RuntimeError:
        logger.warning("No running loop found for MQTT start")

    yield
    # Shutdown
    logger.info("Stopping RL Agent...")
    if rl_agent:
        rl_agent.stop()

    logger.info("Stopping MQTT Service...")
    mqtt_service.stop()

    logger.info("Closing Database...")
    await db_manager.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Universal OEE Interface Backend Running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Send initial state for all known machines
        # Also fetch history for machine_1 (default view)

        # TODO: History fetch needs machine_id
        temp_history = await db_manager.get_telemetry_history("machine_1", "temperature")

        # Construct init payload
        # It's getting large, so maybe just send what's needed.
        # Frontend expects 'init' with single machine data currently.
        # We need to change frontend to handle 'plant_init' or just iterate updates.

        # Let's send a new message type 'plant_state'
        all_machines = machine_manager.get_all_states()

        msg = {
            "type": "plant_init",
            "machines": all_machines,
            "history": temp_history # Default history
        }
        await websocket.send_json(msg)

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.discard(websocket)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

@app.post("/command")
async def send_command(cmd: Command, current_user: User = Depends(get_authorized_user)):
    if not gatekeeper.validate(cmd.command, cmd.target, cmd.signature):
        logger.warning(f"Rejected command: {cmd.command} to {cmd.target} by {current_user.username}")
        raise HTTPException(status_code=403, detail="Command denied by Security Gatekeeper")

    # Audit Log
    await db_manager.log_audit("COMMAND", current_user.username, f"Sent {cmd.command}", signature=cmd.signature)

    logger.info(f"Authorized command: {cmd.command} to {cmd.target} by {current_user.username}")
    mqtt_service.publish(cmd.target, {"command": cmd.command})
    return {"status": "sent", "command": cmd.command}

@app.post("/chat")
async def chat_with_copilot(req: ChatRequest, current_user: User = Depends(get_authorized_user)):
    # Use selected machine if provided, else default to machine_1
    target = req.machine_id if req.machine_id else "machine_1"
    m = machine_manager.get_machine(target)
    context = {
        "oee": m.latest_oee,
        "data": m.current_data,
        "schema": m.schema
    }
    response = chat_agent.process_query(req.query, context)
    return {"response": response}

@app.get("/audit")
async def get_audit_logs(limit: int = 20, current_user: User = Depends(get_authorized_user)):
    return await db_manager.get_audit_logs(limit)

@app.get("/report/pdf")
async def get_report():
    filename = await generate_plant_report()
    return FileResponse(filename, media_type='application/pdf', filename="plant_report.pdf")

@app.get("/machines/{machine_id}/config")
async def get_machine_config(machine_id: str, current_user: User = Depends(get_current_active_user)):
    config = await db_manager.get_machine_config(machine_id)
    if not config:
        # Return default
        return {"machine_id": machine_id, "ideal_cycle_time": 1.0, "shift_start_hour": 8}
    return config

@app.put("/machines/{machine_id}/config")
async def update_machine_config(machine_id: str, config: MachineConfig, current_user: User = Depends(get_authorized_user)):
    # Persist
    await db_manager.update_machine_config(machine_id, config)

    # Update Runtime
    m = machine_manager.get_machine(machine_id)
    m.oee_calculator.set_config(config.dict())

    return {"status": "updated", "config": config}
