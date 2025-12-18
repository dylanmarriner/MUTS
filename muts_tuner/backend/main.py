#!/usr/bin/env python3
"""
MUTS Tuner FastAPI Backend
Oracle server deployment with WebSocket real-time communication
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
import uvicorn
from datetime import datetime
import base64
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MUTS Tuner Backend",
    description="ECU Tuning System Backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ECUData(BaseModel):
    """ECU live data model"""
    timestamp: float
    rpm: Optional[float] = None
    speed: Optional[float] = None
    throttle: Optional[float] = None
    coolant_temp: Optional[float] = None
    intake_temp: Optional[float] = None
    boost: Optional[float] = None
    knock_correction: Optional[float] = None
    afr: Optional[float] = None

class TuneFile(BaseModel):
    """Tune file model"""
    name: str
    description: str
    data: str  # Base64 encoded ROM data
    checksum: str
    created_at: datetime

class VehicleInfo(BaseModel):
    """Vehicle information model"""
    vin: str
    ecu_part_number: str
    calibration_id: str
    software_version: str

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.vehicle_data: Dict[str, Any] = {}
        self.connected_clients: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connected_clients[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to specific client"""
        try:
            await websocket.send_text(message)
        except:
            pass
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

# Global connection manager
manager = ConnectionManager()

# Mock ECU data (will be replaced with real J2534 interface)
class MockECUInterface:
    """Mock ECU interface for testing"""
    
    def __init__(self):
        self.is_connected = False
        self.current_data = ECUData(
            timestamp=0,
            rpm=800,
            speed=0,
            throttle=0,
            coolant_temp=85,
            intake_temp=25,
            boost=0,
            knock_correction=0,
            afr=14.7
        )
    
    async def connect(self) -> bool:
        """Mock connection"""
        await asyncio.sleep(0.5)
        self.is_connected = True
        return True
    
    async def disconnect(self):
        """Mock disconnect"""
        self.is_connected = False
    
    async def read_live_data(self) -> ECUData:
        """Generate mock live data"""
        import time
        import random
        
        if not self.is_connected:
            raise Exception("ECU not connected")
        
        # Simulate realistic engine data
        base_rpm = 800 if self.current_data.speed < 10 else 1500 + self.current_data.speed * 30
        self.current_data.rpm = base_rpm + random.uniform(-50, 50)
        self.current_data.speed = max(0, self.current_data.speed + random.uniform(-2, 2))
        self.current_data.throttle = max(0, min(100, self.current_data.throttle + random.uniform(-5, 5)))
        self.current_data.coolant_temp = max(70, min(110, self.current_data.coolant_temp + random.uniform(-1, 1)))
        self.current_data.intake_temp = max(10, min(60, self.current_data.intake_temp + random.uniform(-2, 2)))
        self.current_data.boost = max(0, min(25, self.current_data.boost + random.uniform(-0.5, 0.5)))
        self.current_data.knock_correction = max(-10, min(10, self.current_data.knock_correction + random.uniform(-1, 1)))
        self.current_data.afr = max(10, min(20, self.current_data.afr + random.uniform(-0.3, 0.3)))
        self.current_data.timestamp = time.time()
        
        return self.current_data

# Initialize mock ECU interface
ecu_interface = MockECUInterface()

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MUTS Tuner Backend API", "status": "running"}

@app.get("/api/status")
async def get_status():
    """Get system status"""
    return {
        "status": "online",
        "ecu_connected": ecu_interface.is_connected,
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/ecu/connect")
async def connect_ecu():
    """Connect to ECU"""
    try:
        success = await ecu_interface.connect()
        if success:
            # Start data streaming
            asyncio.create_task(stream_ecu_data())
            return {"success": True, "message": "ECU connected successfully"}
        else:
            return {"success": False, "message": "Failed to connect to ECU"}
    except Exception as e:
        logger.error(f"ECU connection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ecu/disconnect")
async def disconnect_ecu():
    """Disconnect from ECU"""
    try:
        await ecu_interface.disconnect()
        return {"success": True, "message": "ECU disconnected"}
    except Exception as e:
        logger.error(f"ECU disconnection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ecu/live-data")
async def get_live_data():
    """Get current ECU live data"""
    try:
        if not ecu_interface.is_connected:
            raise HTTPException(status_code=400, detail="ECU not connected")
        
        data = await ecu_interface.read_live_data()
        return data.dict()
    except Exception as e:
        logger.error(f"Live data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vehicle/info")
async def get_vehicle_info():
    """Get vehicle information"""
    # Mock vehicle info
    return VehicleInfo(
        vin="JM1BK143141123456",
        ecu_part_number="L3K9-18-881A",
        calibration_id="L3K918881",
        software_version="V1.0"
    ).dict()

@app.get("/api/tunes")
async def get_tunes():
    """Get available tune files"""
    # Mock tune list
    return {
        "tunes": [
            {
                "id": 1,
                "name": "Stock Tune",
                "description": "Factory calibration",
                "power_gain": 0,
                "fuel_type": "95+",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "name": "Stage 1 Tune",
                "description": "Mild performance tune",
                "power_gain": 30,
                "fuel_type": "95+",
                "created_at": "2024-01-02T00:00:00Z"
            },
            {
                "id": 3,
                "name": "Stage 2 Tune",
                "description": "Medium performance tune",
                "power_gain": 50,
                "fuel_type": "98+",
                "created_at": "2024-01-03T00:00:00Z"
            }
        ]
    }

@app.post("/api/tunes/upload")
async def upload_tune(tune_file: TuneFile):
    """Upload tune file"""
    try:
        # Validate tune file
        decoded_data = base64.b64decode(tune_file.data)
        
        # Save tune file (mock implementation)
        tune_info = {
            "name": tune_file.name,
            "description": tune_file.description,
            "size": len(decoded_data),
            "checksum": tune_file.checksum,
            "uploaded_at": datetime.now().isoformat()
        }
        
        logger.info(f"Tune uploaded: {tune_file.name}")
        return {"success": True, "tune_info": tune_info}
        
    except Exception as e:
        logger.error(f"Tune upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tunes/{tune_id}/flash")
async def flash_tune(tune_id: int):
    """Flash tune to ECU"""
    try:
        if not ecu_interface.is_connected:
            raise HTTPException(status_code=400, detail="ECU not connected")
        
        # Mock flashing process
        logger.info(f"Flashing tune {tune_id} to ECU")
        
        # Simulate flashing progress
        for progress in range(0, 101, 10):
            await asyncio.sleep(0.1)
            await manager.broadcast(json.dumps({
                "type": "flash_progress",
                "progress": progress,
                "message": f"Flashing... {progress}%"
            }))
        
        return {"success": True, "message": "Tune flashed successfully"}
        
    except Exception as e:
        logger.error(f"Tune flash error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diagnostics")
async def get_diagnostics():
    """Get diagnostic information"""
    # Mock DTC data
    return {
        "dtcs": [],
        "readiness_status": {
            "misfire": True,
            "fuel_system": True,
            "components": True,
            "catalyst": True,
            "heated_catalyst": True,
            "evap_system": True,
            "secondary_air": True,
            "ac_refrigerant": True,
            "oxygen_sensor": True,
            "oxygen_sensor_heater": True,
            "egr_system": True
        },
        "last_scan": datetime.now().isoformat()
    }

@app.post("/api/diagnostics/clear")
async def clear_dtcs():
    """Clear diagnostic trouble codes"""
    try:
        if not ecu_interface.is_connected:
            raise HTTPException(status_code=400, detail="ECU not connected")
        
        # Mock DTC clearing
        await asyncio.sleep(1)
        
        return {"success": True, "message": "DTCs cleared successfully"}
        
    except Exception as e:
        logger.error(f"DTC clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                    websocket
                )
            elif message["type"] == "get_live_data":
                if ecu_interface.is_connected:
                    live_data = await ecu_interface.read_live_data()
                    await manager.send_personal_message(
                        json.dumps({"type": "live_data", "data": live_data.dict()}),
                        websocket
                    )
            elif message["type"] == "command":
                # Handle ECU commands
                command = message.get("command")
                if command == "start_data_stream":
                    # Data streaming is handled separately
                    pass
                elif command == "stop_data_stream":
                    # Stop data streaming
                    pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, client_id)

# Background task for streaming ECU data
async def stream_ecu_data():
    """Stream ECU data to all connected clients"""
    while ecu_interface.is_connected:
        try:
            if manager.active_connections:
                # Read live data
                live_data = await ecu_interface.read_live_data()
                
                # Broadcast to all clients
                await manager.broadcast(json.dumps({
                    "type": "live_data",
                    "data": live_data.dict()
                }))
            
            await asyncio.sleep(0.1)  # 10Hz update rate
            
        except Exception as e:
            logger.error(f"Data streaming error: {e}")
            await asyncio.sleep(1)

# Serve static files (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
async def serve_frontend():
    """Serve the frontend application"""
    return FileResponse("static/index.html")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    os.makedirs("static", exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
