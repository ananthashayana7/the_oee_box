from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import asyncio
import json
from collections import deque
from contextlib import asynccontextmanager
from backend.mqtt_client import mqtt_service
from backend.schema_inference import SchemaInferenceEngine
from backend.oee import OEECalculator
from backend.rl_agent import RLAgent
from backend.command_gatekeeper import CommandGatekeeper
from backend.copilot import ChatAgent
from backend.database import db_manager
from backend.alert_engine import alert_engine
from backend.auth import authenticate_user, create_access_token, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models import Token, User
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Global State
schema_engine = SchemaInferenceEngine()
oee_calculator = OEECalculator()
gatekeeper = CommandGatekeeper()
chat_agent = ChatAgent()
rl_agent = None
current_data = {}
latest_oee = {"availability": 0, "performance": 0, "quality": 0, "oee": 0}
connected_websockets = set()
# history = deque(maxlen=60) # Removed in favor of DB

class Command(BaseModel):
    command: str
    target: str = "factory/line1/machine1/command"

class ChatRequest(BaseModel):
    query: str

async def broadcast(message):
    for ws in list(connected_websockets):
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning(f"WebSocket send failed: {e}")
            connected_websockets.discard(ws)

async def handle_mqtt_message(topic, payload):
    global current_data, latest_oee, schema_engine, oee_calculator
    try:
        # Only process data topic for OEE
        if "data" not in topic:
            return

        data = json.loads(payload)
        current_data = data

        # Persist to DB
        timestamp = data.get("timestamp", 0)
        for k, v in data.items():
            if k != "timestamp":
                await db_manager.insert_telemetry(timestamp, k, v)

        # Alerts
        await alert_engine.process(data)
        alerts = await db_manager.get_active_alerts()

        # Process Schema
        schema_engine.process(data)
        schema = schema_engine.get_schema()

        # Calculate OEE (This is stateful)
        oee_result = oee_calculator.update(schema, data)
        if oee_result:
            latest_oee = oee_result

        # Broadcast
        msg = {
            "type": "update",
            "data": current_data,
            "schema": schema,
            "oee": latest_oee,
            "alerts": alerts
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
    # Ensure event loop is set for thread-safe callbacks
    try:
        loop = asyncio.get_running_loop()
        mqtt_service.message_callback = handle_mqtt_message
        mqtt_service.start(loop=loop)

        # Start RL Agent
        logger.info("Starting RL Agent...")
        rl_agent = RLAgent(lambda: latest_oee, mode="shadow")
        asyncio.create_task(rl_agent.start())

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
        # Fetch history from DB for Gauges
        # Ideally we fetch based on schema, but schema might be empty on fresh start.
        # So we just fetch some known keys or recently active ones?
        # For simplicity in this demo, let's fetch 'temperature' if it exists.
        # Or better: construct history from DB.

        # TODO: A better way is to fetch distinct timestamps and pivot.
        # For now, let's just send an empty history and let the frontend build it up,
        # OR implement a proper history fetch.
        # Let's try to fetch 'temperature' as a proxy for history.

        temp_history = await db_manager.get_telemetry_history("temperature")
        # Transform to frontend format: [{timestamp: ..., temperature: ...}]
        # This is partial history (only temp).

        initial_msg = {
            "type": "init",
            "data": current_data,
            "schema": schema_engine.get_schema(),
            "oee": latest_oee,
            "history": temp_history # This will only populate the Temperature chart
        }
        await websocket.send_json(initial_msg)
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
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/command")
async def send_command(cmd: Command, current_user: User = Depends(get_current_active_user)):
    if not gatekeeper.validate(cmd.command, cmd.target):
        logger.warning(f"Rejected command: {cmd.command} to {cmd.target} by {current_user.username}")
        raise HTTPException(status_code=403, detail="Command denied by Security Gatekeeper")

    # Audit Log
    await db_manager.log_audit("COMMAND", current_user.username, f"Sent {cmd.command}")

    logger.info(f"Authorized command: {cmd.command} to {cmd.target} by {current_user.username}")
    mqtt_service.publish(cmd.target, {"command": cmd.command})
    return {"status": "sent", "command": cmd.command}

@app.post("/chat")
async def chat_with_copilot(req: ChatRequest):
    context = {
        "oee": latest_oee,
        "data": current_data,
        "schema": schema_engine.get_schema()
    }
    response = chat_agent.process_query(req.query, context)
    return {"response": response}

@app.get("/audit")
async def get_audit_logs(limit: int = 20):
    return await db_manager.get_audit_logs(limit)
