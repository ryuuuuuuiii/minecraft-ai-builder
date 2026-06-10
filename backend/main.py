import asyncio
import json
import os
import uuid
import re
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
import websockets
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from pydantic import BaseModel

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
WS_HOST      = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT      = int(os.getenv("WS_PORT", "8080"))
API_HOST     = os.getenv("API_HOST", "0.0.0.0")
API_PORT     = int(os.getenv("API_PORT", "8000"))

SYSTEM_PROMPT = """You are a Minecraft Bedrock Edition command expert.
When the user describes a building or structure, respond with ONLY valid JSON in this exact format:
{"commands": ["command1", "command2", ...]}

Rules:
- Do NOT include a slash (/) at the start of any command
- Use setblock with relative coordinates (~) from the player's position
- Start building at ~2 ~0 ~0 so the structure appears in front of the player
- Use only valid Minecraft Bedrock block names (e.g. log, planks, stone, cobblestone, glass, etc.)
- For log blocks use: log or log2 (not oak_log)
- For planks use: planks (not oak_planks)
- For cobblestone use: cobblestone
- For glass use: glass
- For doors: use blocks with state notation if needed
- Build hollow structures when possible to reduce command count
- Keep command list under 200 commands
- Respond with ONLY the JSON object, no explanation, no markdown, no code fences"""

# ── Global state ──────────────────────────────────────────────────────────────
minecraft_ws: Optional[websockets.WebSocketServerProtocol] = None
pending_responses: dict[str, asyncio.Future] = {}
build_log: list[dict] = []

# ── Groq client ───────────────────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)


# ── WebSocket server (Minecraft side) ─────────────────────────────────────────
def make_command_packet(command: str, request_id: str) -> str:
    """Build the JSON packet format Minecraft Bedrock WebSocket expects."""
    return json.dumps({
        "header": {
            "version": 1,
            "requestId": request_id,
            "messageType": "commandRequest",
            "messagePurpose": "commandRequest",
        },
        "body": {
            "origin": {"type": "player"},
            "commandLine": command,
            "version": 1,
        },
    })


async def minecraft_handler(websocket: websockets.WebSocketServerProtocol):
    """Handle a Minecraft Bedrock client connection."""
    global minecraft_ws
    minecraft_ws = websocket
    client_addr = websocket.remote_address
    print(f"[WS] Minecraft connected from {client_addr}")

    try:
        async for raw in websocket:
            try:
                packet = json.loads(raw)
                request_id = packet.get("header", {}).get("requestId", "")
                if request_id and request_id in pending_responses:
                    fut = pending_responses[request_id]
                    if not fut.done():
                        fut.set_result(packet)
            except json.JSONDecodeError:
                pass
    except websockets.exceptions.ConnectionClosed:
        print(f"[WS] Minecraft disconnected from {client_addr}")
    finally:
        if minecraft_ws is websocket:
            minecraft_ws = None


async def send_command(command: str, timeout: float = 10.0) -> dict:
    """Send a single command to Minecraft and await its response."""
    if minecraft_ws is None:
        return {"success": False, "error": "Minecraft tidak terhubung"}

    request_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    fut: asyncio.Future = loop.create_future()
    pending_responses[request_id] = fut

    try:
        packet = make_command_packet(command, request_id)
        await minecraft_ws.send(packet)
        response = await asyncio.wait_for(fut, timeout=timeout)
        status_code = response.get("body", {}).get("statusCode", -1)
        status_msg  = response.get("body", {}).get("statusMessage", "")
        return {
            "success": status_code == 0,
            "statusCode": status_code,
            "message": status_msg,
        }
    except asyncio.TimeoutError:
        return {"success": False, "error": "Timeout – Minecraft tidak merespons"}
    except websockets.exceptions.ConnectionClosed:
        return {"success": False, "error": "Koneksi Minecraft terputus saat eksekusi"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        pending_responses.pop(request_id, None)


def clean_command(cmd: str) -> str:
    """Strip leading slash and 'execute at X run' wrappers if present."""
    cmd = cmd.strip()
    # Remove leading slash
    if cmd.startswith("/"):
        cmd = cmd[1:]
    # Remove "execute at @s run " prefix that some models add
    cmd = re.sub(r"^execute\s+at\s+\S+\s+run\s+", "", cmd, flags=re.IGNORECASE)
    return cmd.strip()


# ── FastAPI app ───────────────────────────────────────────────────────────────
@app.websocket("/ws/minecraft")
async def minecraft_ws_endpoint(websocket: WebSocket):
    global minecraft_ws
    await websocket.accept()
    minecraft_ws = websocket
    print(f"[WS] Minecraft connected from {websocket.client}")


app = FastAPI(title="Minecraft AI Builder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BuildRequest(BaseModel):
    prompt: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/status")
async def get_status():
    return {"connected": minecraft_ws is not None}


@app.post("/build")
async def build(req: BuildRequest):
    global build_log
    build_log = []

    if not GROQ_API_KEY:
        return {"success": False, "error": "GROQ_API_KEY tidak ditemukan di .env", "log": []}

    if minecraft_ws is None:
        return {"success": False, "error": "Minecraft belum terhubung. Hubungkan dulu via /connect", "log": []}

    # Step 1: Ask Groq to generate commands
    try:
        chat = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": req.prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw_content = chat.choices[0].message.content.strip()
    except Exception as e:
        return {"success": False, "error": f"Groq API error: {e}", "log": []}

    # Step 2: Parse JSON response
    try:
        # Strip markdown code fences if model wraps it anyway
        clean_json = re.sub(r"```(?:json)?|```", "", raw_content).strip()
        data = json.loads(clean_json)
        commands: list[str] = data.get("commands", [])
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"AI mengembalikan respons tidak valid: {e}",
            "raw": raw_content,
            "log": [],
        }

    if not commands:
        return {"success": False, "error": "AI tidak menghasilkan command apapun", "log": []}

    # Step 3: Send each command to Minecraft
    results = []
    for i, cmd in enumerate(commands):
        cmd = clean_command(cmd)
        if not cmd:
            continue

        result = await send_command(cmd)
        entry = {
            "index": i + 1,
            "command": cmd,
            "success": result.get("success", False),
            "message": result.get("message") or result.get("error", ""),
        }
        results.append(entry)

        # If Minecraft disconnected mid-build, stop
        if not result.get("success") and "terputus" in result.get("error", ""):
            break

    build_log = results
    total   = len(results)
    success = sum(1 for r in results if r["success"])
    return {
        "success": True,
        "total": total,
        "succeeded": success,
        "failed": total - success,
        "log": results,
    }


@app.get("/log")
async def get_log():
    return {"log": build_log}


if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=False)
