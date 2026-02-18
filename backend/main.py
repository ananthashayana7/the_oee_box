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
from fastapi import HTTPException

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
history = deque(maxlen=60) # Store last 60 data points

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
    global current_data, latest_oee, schema_engine, oee_calculator, history
    try:
        # Only process data topic for OEE
        if "data" not in topic:
            return

        data = json.loads(payload)
        current_data = data
        history.append(data)

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
            "oee": latest_oee
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
    logger.info("Starting MQTT Service...")
    # Ensure event loop is set for thread-safe callbacks
    try:
        loop = asyncio.get_running_loop()
        mqtt_service.message_callback = handle_mqtt_message
        mqtt_service.start(loop=loop)

        # Start RL Agent
        logger.info("Starting RL Agent...")
        rl_agent = RLAgent(lambda: latest_oee)
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
        # Send initial state + History
        initial_msg = {
            "type": "init",
            "data": current_data,
            "schema": schema_engine.get_schema(),
            "oee": latest_oee,
            "history": list(history)
        }
        await websocket.send_json(initial_msg)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.discard(websocket)

@app.post("/command")
async def send_command(cmd: Command):
    if not gatekeeper.validate(cmd.command, cmd.target):
        logger.warning(f"Rejected command: {cmd.command} to {cmd.target}")
        raise HTTPException(status_code=403, detail="Command denied by Security Gatekeeper")

    logger.info(f"Authorized command: {cmd.command} to {cmd.target}")
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
