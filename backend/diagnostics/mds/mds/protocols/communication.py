#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAN INTERFACE - Complete CAN Bus Communication
Direct CAN interface implementation for Mazda vehicles
"""

import socket
import struct
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from enum import IntEnum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CANFrameType(IntEnum):
    """CAN Frame Types"""
    STANDARD = 0x01  # 11-bit identifier
    EXTENDED = 0x02  # 29-bit identifier
    REMOTE = 0x03    # Remote transmission request
    ERROR = 0x04     # Error frame

@dataclass
class CANFrame:
    """CAN Frame Structure"""
    frame_id: int
    data: bytes
    frame_type: CANFrameType = CANFrameType.STANDARD
    timestamp: float = 0.0
    interface: str = "can0"

class MazdaCommunication:
    """
    Complete CAN Interface for Mazda Vehicle Communication
    Provides direct CAN bus access for advanced diagnostics
    """
    
    def __init__(self, interface: str = "can0", bitrate: int = 500000):
        self.interface = interface
        self.bitrate = bitrate
        self.socket = None
        self.is_connected = False
        self.receive_callback = None
        self.receive_thread = None
        self.receive_running = False
        
        # Mazda-specific CAN addresses
        self.mazda_addresses = {
            'ECU_TX': 0x7E0,
            'ECU_RX': 0x7E8,
            'TCM_TX': 0x7E1,
            'TCM_RX': 0x7E9,
            'ABS_TX': 0x7E2,
            'ABS_RX': 0x7EA,
            'BCM_TX': 0x7E6,
            'BCM_RX': 0x7EE,
            'GATEWAY_TX': 0x750,
            'GATEWAY_RX': 0x758
        }
        
    def connect(self) -> bool:
        """
        Connect to CAN interface
        
        Returns:
            True if connection successful
        """
        try:
            logger.info(f"Connecting to CAN interface: {self.interface}")
            
            # Create raw CAN socket
            self.socket = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
            
            # Bind to interface
            self.socket.bind((self.interface,))
            
            # Set up filters (optional - receive all frames)
            self._setup_can_filters()
            
            self.is_connected = True
            logger.info(f"Successfully connected to CAN interface: {self.interface}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to CAN interface: {e}")
            self.is_connected = False
            return False
    
    def _setup_can_filters(self):
        """Setup CAN frame filters"""
        try:
            # Setup filter to receive all frames
            # In production, you might want to filter specific frames
            pass
            
        except Exception as e:
            logger.warning(f"Could not setup CAN filters: {e}")
    
    def disconnect(self):
        """Disconnect from CAN interface"""
        try:
            if self.receive_running:
                self.stop_receiving()
            
            if self.socket:
                self.socket.close()
                self.socket = None
            
            self.is_connected = False
            logger.info("Disconnected from CAN interface")
            
        except Exception as e:
            logger.error(f"Error disconnecting from CAN interface: {e}")
    
    def send_frame(self, frame: CANFrame) -> bool:
        """
        Send CAN frame
        
        Args:
            frame: CAN frame to send
            
        Returns:
            True if successful
        """
        try:
            if not self.is_connected or not self.socket:
                logger.error("CAN interface not connected")
                return False
            
            # Build CAN frame
            can_id = frame.frame_id
            if frame.frame_type == CANFrameType.EXTENDED:
                can_id |= socket.CAN_EFF_FLAG
            
            # Create CAN frame structure
            can_frame = struct.pack("=IB3x8s", can_id, len(frame.data), frame.data)
            
            # Send frame
            self.socket.send(can_frame)
            
            logger.debug(f"Sent CAN frame: ID=0x{frame.frame_id:03X}, Data={frame.data.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending CAN frame: {e}")
            return False
    
    def receive_frame(self, timeout: float = 1.0) -> Optional[CANFrame]:
        """
        Receive CAN frame
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            Received CAN frame or None
        """
        try:
            if not self.is_connected or not self.socket:
                return None
            
            # Set socket timeout
            self.socket.settimeout(timeout)
            
            # Receive frame
            can_frame, _ = self.socket.recvfrom(16)
            
            # Parse frame
            can_id, can_dlc, data = struct.unpack("=IB3x8s", can_frame)
            
            # Determine frame type
            frame_type = CANFrameType.STANDARD
            if can_id & socket.CAN_EFF_FLAG:
                frame_type = CANFrameType.EXTENDED
                can_id &= ~socket.CAN_EFF_FLAG
            
            # Create CAN frame object
            frame = CANFrame(
                frame_id=can_id,
                data=data[:can_dlc],
                frame_type=frame_type,
                timestamp=time.time(),
                interface=self.interface
            )
            
            logger.debug(f"Received CAN frame: ID=0x{frame.frame_id:03X}, Data={frame.data.hex()}")
            return frame
            
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving CAN frame: {e}")
            return None
    
    def start_receiving(self, callback: Callable[[CANFrame], None]):
        """
        Start receiving frames in background thread
        
        Args:
            callback: Callback function for received frames
        """
        try:
            if self.receive_running:
                logger.warning("Already receiving CAN frames")
                return
            
            self.receive_callback = callback
            self.receive_running = True
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            logger.info("Started receiving CAN frames")
            
        except Exception as e:
            logger.error(f"Error starting CAN receive: {e}")
    
    def stop_receiving(self):
        """Stop receiving frames"""
        try:
            self.receive_running = False
            
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)
            
            logger.info("Stopped receiving CAN frames")
            
        except Exception as e:
            logger.error(f"Error stopping CAN receive: {e}")
    
    def _receive_loop(self):
        """Receive loop for background thread"""
        while self.receive_running:
            try:
                frame = self.receive_frame(timeout=0.1)
                if frame and self.receive_callback:
                    self.receive_callback(frame)
                    
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                time.sleep(0.1)
    
    def send_diagnostic_message(self, target_ecu: str, service_id: int, 
                              data: bytes = b'') -> bool:
        """
        Send diagnostic message over CAN
        
        Args:
            target_ecu: Target ECU (e.g., 'ECU', 'TCM', 'ABS')
            service_id: Diagnostic service ID
            data: Service data
            
        Returns:
            True if successful
        """
        try:
            # Get target address
            tx_address = self.mazda_addresses.get(f"{target_ecu}_TX")
            if not tx_address:
                logger.error(f"Unknown ECU: {target_ecu}")
                return False
            
            # Build diagnostic message
            message_data = bytes([service_id]) + data
            
            # Create CAN frame
            frame = CANFrame(
                frame_id=tx_address,
                data=message_data,
                timestamp=time.time()
            )
            
            # Send frame
            return self.send_frame(frame)
            
        except Exception as e:
            logger.error(f"Error sending diagnostic message: {e}")
            return False
    
    def wait_for_response(self, source_ecu: str, timeout: float = 2.0) -> Optional[CANFrame]:
        """
        Wait for diagnostic response
        
        Args:
            source_ecu: Source ECU to wait for
            timeout: Timeout in seconds
            
        Returns:
            Response frame or None
        """
        try:
            # Get source address
            rx_address = self.mazda_addresses.get(f"{source_ecu}_RX")
            if not rx_address:
                logger.error(f"Unknown ECU: {source_ecu}")
                return None
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                frame = self.receive_frame(timeout=0.1)
                if frame and frame.frame_id == rx_address:
                    return frame
            
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for response: {e}")
            return None
    
    def get_interface_status(self) -> Dict[str, Any]:
        """
        Get CAN interface status
        
        Returns:
            Interface status information
        """
        return {
            'interface': self.interface,
            'bitrate': self.bitrate,
            'connected': self.is_connected,
            'receiving': self.receive_running,
            'mazda_addresses': self.mazda_addresses
        }
    
    def send_mazda_specific_command(self, command: bytes, target: str = 'ECU') -> bool:
        """
        Send Mazda-specific command
        
        Args:
            command: Command bytes
            target: Target ECU
            
        Returns:
            True if successful
        """
        try:
            # Mazda commands use special format
            # Prefix with Mazda identifier
            mazda_command = b'\xMAZDA' + command
            
            return self.send_diagnostic_message(target, 0x3E, mazda_command)
            
        except Exception as e:
            logger.error(f"Error sending Mazda command: {e}")
            return False
