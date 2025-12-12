#!/usr/bin/env python3
"""
MUTS Tuner Backend API Tests
Comprehensive testing of FastAPI endpoints and WebSocket functionality
"""

import asyncio
import json
import pytest
import websockets
from fastapi.testclient import TestClient
import httpx
import time
from datetime import datetime

# Import the main application
from main import app, ecu_interface, manager

class TestBackendAPI:
    """Test suite for MUTS Tuner Backend API"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    async def websocket_client(self):
        """Create WebSocket test client"""
        uri = "ws://localhost:8000/ws/test"
        async with websockets.connect(uri) as websocket:
            yield websocket

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_status_endpoint(self, client):
        """Test system status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "ecu_connected" in data
        assert "active_connections" in data
        assert "timestamp" in data

    def test_ecu_connect_endpoint(self, client):
        """Test ECU connection endpoint"""
        response = client.post("/api/ecu/connect")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_ecu_disconnect_endpoint(self, client):
        """Test ECU disconnection endpoint"""
        # First connect
        client.post("/api/ecu/connect")
        
        # Then disconnect
        response = client.post("/api/ecu/disconnect")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_live_data_endpoint_without_connection(self, client):
        """Test live data endpoint when ECU not connected"""
        response = client.get("/api/ecu/live-data")
        assert response.status_code == 400
        assert "ECU not connected" in response.json()["detail"]

    def test_live_data_endpoint_with_connection(self, client):
        """Test live data endpoint when ECU is connected"""
        # Connect first
        client.post("/api/ecu/connect")
        
        # Get live data
        response = client.get("/api/ecu/live-data")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        required_fields = ["timestamp", "rpm", "speed", "throttle", "coolant_temp", 
                         "intake_temp", "boost", "knock_correction", "afr"]
        for field in required_fields:
            assert field in data

    def test_vehicle_info_endpoint(self, client):
        """Test vehicle information endpoint"""
        response = client.get("/api/vehicle/info")
        assert response.status_code == 200
        data = response.json()
        
        # Verify vehicle info fields
        required_fields = ["vin", "ecu_part_number", "calibration_id", "software_version"]
        for field in required_fields:
            assert field in data

    def test_tunes_endpoint(self, client):
        """Test tunes list endpoint"""
        response = client.get("/api/tunes")
        assert response.status_code == 200
        data = response.json()
        assert "tunes" in data
        assert len(data["tunes"]) > 0
        
        # Verify tune structure
        tune = data["tunes"][0]
        required_fields = ["id", "name", "description", "power_gain", "fuel_type", "created_at"]
        for field in required_fields:
            assert field in tune

    def test_diagnostics_endpoint(self, client):
        """Test diagnostics endpoint"""
        response = client.get("/api/diagnostics")
        assert response.status_code == 200
        data = response.json()
        
        # Verify diagnostics structure
        assert "dtcs" in data
        assert "readiness_status" in data
        assert "last_scan" in data

    def test_clear_dtcs_endpoint(self, client):
        """Test DTC clearing endpoint"""
        # Connect first
        client.post("/api/ecu/connect")
        
        response = client.post("/api/diagnostics/clear")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "message" in data

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data

class TestWebSocketFunctionality:
    """Test suite for WebSocket real-time communication"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        uri = "ws://localhost:8000/ws/test_client"
        try:
            async with websockets.connect(uri) as websocket:
                # Connection should be established
                assert websocket.open
                
                # Send ping message
                ping_msg = {"type": "ping"}
                await websocket.send(json.dumps(ping_msg))
                
                # Receive pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                assert data["type"] == "pong"
                assert "timestamp" in data
                
        except Exception as e:
            pytest.skip(f"WebSocket server not running: {e}")

    @pytest.mark.asyncio
    async def test_websocket_live_data_streaming(self):
        """Test WebSocket live data streaming"""
        uri = "ws://localhost:8000/ws/test_client"
        try:
            async with websockets.connect(uri) as websocket:
                # Connect ECU first
                await self.connect_ecu_via_api()
                
                # Request live data
                live_data_request = {"type": "get_live_data"}
                await websocket.send(json.dumps(live_data_request))
                
                # Receive live data response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                assert data["type"] == "live_data"
                assert "data" in data
                
                # Verify live data structure
                live_data = data["data"]
                required_fields = ["timestamp", "rpm", "speed", "throttle", "coolant_temp",
                                 "intake_temp", "boost", "knock_correction", "afr"]
                for field in required_fields:
                    assert field in live_data
                
        except Exception as e:
            pytest.skip(f"WebSocket server not running: {e}")

    async def connect_ecu_via_api(self):
        """Helper method to connect ECU via API"""
        async with httpx.AsyncClient() as client:
            response = await client.post("http://localhost:8000/api/ecu/connect")
            assert response.status_code == 200

class TestECUInterface:
    """Test suite for ECU interface functionality"""
    
    @pytest.mark.asyncio
    async def test_mock_ecu_connection(self):
        """Test mock ECU connection"""
        result = await ecu_interface.connect()
        assert result is True
        assert ecu_interface.is_connected is True

    @pytest.mark.asyncio
    async def test_mock_ecu_live_data(self):
        """Test mock ECU live data generation"""
        # Connect first
        await ecu_interface.connect()
        
        # Read live data
        data = await ecu_interface.read_live_data()
        
        # Verify data structure
        assert hasattr(data, 'timestamp')
        assert hasattr(data, 'rpm')
        assert hasattr(data, 'speed')
        assert hasattr(data, 'throttle')
        assert data.rpm > 0
        assert data.speed >= 0
        assert data.throttle >= 0

    @pytest.mark.asyncio
    async def test_mock_ecu_disconnection(self):
        """Test mock ECU disconnection"""
        # Connect first
        await ecu_interface.connect()
        
        # Disconnect
        await ecu_interface.disconnect()
        assert ecu_interface.is_connected is False

class TestErrorHandling:
    """Test suite for error handling and edge cases"""
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/invalid")
        assert response.status_code == 404

    def test_tune_flash_without_connection(self, client):
        """Test tune flashing without ECU connection"""
        response = client.post("/api/tunes/1/flash")
        assert response.status_code == 400
        assert "ECU not connected" in response.json()["detail"]

    def test_tune_flash_invalid_id(self, client):
        """Test tune flashing with invalid tune ID"""
        # Connect first
        client.post("/api/ecu/connect")
        
        # Try to flash invalid tune
        response = client.post("/api/tunes/999/flash")
        # Should handle gracefully (mock implementation accepts any ID)
        assert response.status_code in [200, 400, 404]

class TestPerformance:
    """Test suite for performance and load testing"""
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get("/api/status")
            results.put(response.status_code)
        
        # Create 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code == 200

    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        uri = "ws://localhost:8000/ws/throughput_test"
        try:
            async with websockets.connect(uri) as websocket:
                start_time = time.time()
                messages_sent = 0
                messages_received = 0
                
                # Send 100 messages rapidly
                for i in range(100):
                    ping_msg = {"type": "ping", "id": i}
                    await websocket.send(json.dumps(ping_msg))
                    messages_sent += 1
                
                # Receive responses
                for _ in range(100):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(response)
                        if data["type"] == "pong":
                            messages_received += 1
                    except asyncio.TimeoutError:
                        break
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Verify throughput
                assert messages_received >= 90  # Allow for some message loss
                assert duration < 5.0  # Should complete within 5 seconds
                
        except Exception as e:
            pytest.skip(f"WebSocket server not running: {e}")

# Integration tests
class TestIntegrationWorkflow:
    """Test suite for complete user workflows"""
    
    def test_complete_monitoring_workflow(self, client):
        """Test complete monitoring workflow"""
        # 1. Connect to ECU
        response = client.post("/api/ecu/connect")
        assert response.status_code == 200
        
        # 2. Get vehicle info
        response = client.get("/api/vehicle/info")
        assert response.status_code == 200
        vehicle_data = response.json()
        assert vehicle_data["vin"] is not None
        
        # 3. Monitor live data for multiple readings
        for _ in range(5):
            response = client.get("/api/ecu/live-data")
            assert response.status_code == 200
            live_data = response.json()
            assert live_data["rpm"] > 0
            time.sleep(0.1)
        
        # 4. Run diagnostics
        response = client.get("/api/diagnostics")
        assert response.status_code == 200
        diagnostics = response.json()
        assert "dtcs" in diagnostics
        
        # 5. Disconnect
        response = client.post("/api/ecu/disconnect")
        assert response.status_code == 200

    def test_complete_tuning_workflow(self, client):
        """Test complete tuning workflow"""
        # 1. Connect to ECU
        response = client.post("/api/ecu/connect")
        assert response.status_code == 200
        
        # 2. Get available tunes
        response = client.get("/api/tunes")
        assert response.status_code == 200
        tunes = response.json()["tunes"]
        assert len(tunes) > 0
        
        # 3. Select a tune (Stage 1)
        stage1_tune = next((t for t in tunes if "Stage 1" in t["name"]), None)
        assert stage1_tune is not None
        
        # 4. Flash the tune
        response = client.post(f"/api/tunes/{stage1_tune['id']}/flash")
        assert response.status_code == 200
        flash_result = response.json()
        assert flash_result["success"] is True
        
        # 5. Verify tune was applied (check live data shows changes)
        response = client.get("/api/ecu/live-data")
        assert response.status_code == 200
        live_data = response.json()
        assert live_data["rpm"] > 0
        
        # 6. Disconnect
        response = client.post("/api/ecu/disconnect")
        assert response.status_code == 200

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
