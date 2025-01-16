from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from quantum_protocol import QuantumProtocol
from fastapi.responses import HTMLResponse, FileResponse
import os
import logging
import warnings
import ssl
from pathlib import Path
import asyncio

# Suppress warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=ImportWarning)
warnings.filterwarnings('ignore', module='dateutil')

app = FastAPI()
templates = Jinja2Templates(directory="templates")
quantum_protocol = QuantumProtocol()

# Define ConnectionManager class before using it
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

# Create manager instance after class definition
manager = ConnectionManager()
quantum_protocol.set_manager(manager)  # Set the manager

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add these settings near the top after app initialization
ssl_keyfile = Path("key.pem")  # Your SSL key file
ssl_certfile = Path("cert.pem")  # Your SSL certificate file

# Generate self-signed certificate if not exists
if not (ssl_keyfile.exists() and ssl_certfile.exists()):
    from OpenSSL import crypto
    
    # Generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # Save certificate and private key
    with open(ssl_certfile, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(ssl_keyfile, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    protocol = "wss" if request.url.scheme == "https" else "ws"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "websocket_url": f"{protocol}://{request.headers.get('host')}/ws"
        }
    )

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    websocket.client_id = client_id
    
    async def check_key_rotation():
        while True:
            try:
                await asyncio.sleep(1)  # Check more frequently
                active_sessions = list(quantum_protocol.session_keys.keys())
                for session_id in active_sessions:
                    await quantum_protocol.check_and_rotate_keys(session_id)
            except Exception as e:
                logger.error(f"Error in key rotation: {str(e)}")
    
    # Start key rotation checker
    rotation_task = asyncio.create_task(check_key_rotation())
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received data from {client_id}: {data}")
            
            if data["type"] == "start_key_exchange":
                partner_id = data["partner_id"]
                logger.info(f"Starting key exchange between {client_id} and {partner_id}")
                
                if partner_id in manager.active_connections:
                    partner_ws = manager.active_connections[partner_id]
                    success = await quantum_protocol.generate_key(websocket, partner_ws)
                    
                    if success:
                        logger.info(f"Key exchange successful between {client_id} and {partner_id}")
                    else:
                        logger.error(f"Key exchange failed between {client_id} and {partner_id}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Key exchange failed"
                        })
                else:
                    logger.warning(f"Partner {partner_id} not found")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Partner {partner_id} not found"
                    })
            
            elif data["type"] == "encrypted_message":
                if "to" not in data or "message" not in data:
                    continue
                    
                partner_id = data["to"]
                if partner_id in manager.active_connections:
                    partner_ws = manager.active_connections[partner_id]
                    success = await quantum_protocol.broadcast_message(websocket, partner_ws, data)
                    if not success:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to send message"
                        })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Partner {partner_id} not found"
                    })
            
    except WebSocketDisconnect:
        rotation_task.cancel()  # Cancel the rotation task
        manager.disconnect(client_id)
    except Exception as e:
        rotation_task.cancel()  # Cancel the rotation task
        logger.error(f"Error in websocket endpoint: {str(e)}", exc_info=True)
        manager.disconnect(client_id)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(
        os.path.join(os.path.dirname(__file__), 'static', 'favicon.ico'),
        media_type='image/vnd.microsoft.icon'
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        ssl_keyfile=str(ssl_keyfile),
        ssl_certfile=str(ssl_certfile)
    ) 