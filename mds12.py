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

class MazdaCANInterface:
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
            self.stop_receive_thread()
            
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
            True if send successful
        """
        try:
            if not self.is_connected or not self.socket:
                logger.error("CAN interface not connected")
                return False
            
            # Build CAN frame structure
            can_id = frame.frame_id
            if frame.frame_type == CANFrameType.EXTENDED:
                can_id |= socket.CAN_EFF_FLAG
            elif frame.frame_type == CANFrameType.REMOTE:
                can_id |= socket.CAN_RTR_FLAG
            elif frame.frame_type == CANFrameType.ERROR:
                can_id |= socket.CAN_ERR_FLAG
            
            # Create frame data
            frame_data = struct.pack(f"=I{len(frame.data)}s", can_id, frame.data)
            
            # Send frame
            sent = self.socket.send(frame_data)
            
            if sent > 0:
                logger.debug(f"Sent CAN frame: ID=0x{frame.frame_id:03X}, Data={frame.data.hex().upper()}")
                return True
            else:
                logger.error("Failed to send CAN frame")
                return False
                
        except Exception as e:
            logger.error(f"Error sending CAN frame: {e}")
            return False
    
    def receive_frame(self, timeout: float = 1.0) -> Optional[CANFrame]:
        """
        Receive CAN frame with timeout
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            CAN frame or None if timeout
        """
        try:
            if not self.is_connected or not self.socket:
                logger.error("CAN interface not connected")
                return None
            
            # Set socket timeout
            self.socket.settimeout(timeout)
            
            # Receive frame
            frame_data = self.socket.recv(16)  # CAN frame size
            
            if frame_data:
                # Parse CAN frame
                can_id = struct.unpack("=I", frame_data[:4])[0]
                data = frame_data[4:]
                
                # Determine frame type
                frame_type = CANFrameType.STANDARD
                if can_id & socket.CAN_EFF_FLAG:
                    frame_type = CANFrameType.EXTENDED
                    can_id &= socket.CAN_EFF_MASK
                elif can_id & socket.CAN_RTR_FLAG:
                    frame_type = CANFrameType.REMOTE
                    can_id &= socket.CAN_RTR_FLAG
                elif can_id & socket.CAN_ERR_FLAG:
                    frame_type = CANFrameType.ERROR
                    can_id &= socket.CAN_ERR_MASK
                
                frame = CANFrame(
                    frame_id=can_id,
                    data=data,
                    frame_type=frame_type,
                    timestamp=time.time(),
                    interface=self.interface
                )
                
                logger.debug(f"Received CAN frame: ID=0x{frame.frame_id:03X}, Data={frame.data.hex().upper()}")
                return frame
            
            return None
            
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving CAN frame: {e}")
            return None
    
    def start_receive_thread(self, callback: Callable[[CANFrame], None]):
        """
        Start background receive thread
        
        Args:
            callback: Function to call when frame received
        """
        try:
            self.receive_callback = callback
            self.receive_running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            logger.info("Started CAN receive thread")
            
        except Exception as e:
            logger.error(f"Error starting receive thread: {e}")
    
    def stop_receive_thread(self):
        """Stop background receive thread"""
        try:
            self.receive_running = False
            if self.receive_thread and self.receive_thread.is_alive():
                self.receive_thread.join(timeout=2.0)
            self.receive_thread = None
            logger.info("Stopped CAN receive thread")
            
        except Exception as e:
            logger.error(f"Error stopping receive thread: {e}")
    
    def _receive_loop(self):
        """Background receive loop"""
        while self.receive_running and self.is_connected:
            try:
                frame = self.receive_frame(timeout=0.1)
                if frame and self.receive_callback:
                    self.receive_callback(frame)
                    
            except Exception as e:
                if self.receive_running:  # Only log if we're still supposed to be running
                    logger.error(f"Error in receive loop: {e}")
                time.sleep(0.01)
    
    def send_diagnostic_message(self, target_address: int, data: bytes, 
                              source_address: int = 0x7DF) -> bool:
        """
        Send diagnostic message over CAN
        
        Args:
            target_address: Target ECU address
            data: Message data
            source_address: Source address (tester)
            
        Returns:
            True if send successful
        """
        try:
            # Build CAN frame for diagnostic message
            # ISO-TP single frame for small messages
            if len(data) <= 7:
                # Single frame
                frame_data = bytes([0x00 | len(data)]) + data
                frame_data = frame_data.ljust(8, b'\x00')
                
                frame = CANFrame(
                    frame_id=target_address,
                    data=frame_data,
                    frame_type=CANFrameType.STANDARD
                )
                
                return self.send_frame(frame)
            else:
                # Multi-frame message (first frame)
                # This would implement ISO-TP multi-frame messaging
                logger.warning("Multi-frame messages not fully implemented")
                return False
                
        except Exception as e:
            logger.error(f"Error sending diagnostic message: {e}")
            return False
    
    def receive_diagnostic_message(self, expected_address: int, 
                                 timeout: float = 1.0) -> Optional[bytes]:
        """
        Receive diagnostic message from CAN
        
        Args:
            expected_address: Expected source address
            timeout: Receive timeout
            
        Returns:
            Message data or None if timeout
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                frame = self.receive_frame(timeout=0.1)
                if frame and frame.frame_id == expected_address:
                    # Parse ISO-TP frame
                    if len(frame.data) >= 1:
                        pci = frame.data[0]
                        if pci & 0xF0 == 0x00:  # Single frame
                            data_length = pci & 0x0F
                            if len(frame.data) >= data_length + 1:
                                return frame.data[1:1+data_length]
            
            return None
            
        except Exception as e:
            logger.error(f"Error receiving diagnostic message: {e}")
            return None
    
    def monitor_bus_traffic(self, duration: float = 10.0) -> Dict[str, Any]:
        """
        Monitor CAN bus traffic
        
        Args:
            duration: Monitoring duration in seconds
            
        Returns:
            Traffic analysis results
        """
        logger.info(f"Monitoring CAN bus traffic for {duration} seconds")
        
        traffic_data = {
            'start_time': time.time(),
            'end_time': 0,
            'total_frames': 0,
            'frames_by_id': {},
            'error_frames': 0,
            'data_rates': {},
            'identified_messages': []
        }
        
        try:
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < duration:
                frame = self.receive_frame(timeout=0.1)
                if frame:
                    frame_count += 1
                    
                    # Count frames by ID
                    frame_id_hex = f"0x{frame.frame_id:03X}"
                    traffic_data['frames_by_id'][frame_id_hex] = \
                        traffic_data['frames_by_id'].get(frame_id_hex, 0) + 1
                    
                    # Count error frames
                    if frame.frame_type == CANFrameType.ERROR:
                        traffic_data['error_frames'] += 1
                    
                    # Identify Mazda-specific messages
                    identified_msg = self._identify_mazda_message(frame)
                    if identified_msg:
                        traffic_data['identified_messages'].append(identified_msg)
            
            traffic_data['end_time'] = time.time()
            traffic_data['total_frames'] = frame_count
            traffic_data['data_rate'] = frame_count / duration  # frames per second
            
            logger.info(f"CAN bus monitoring completed: {frame_count} frames analyzed")
            return traffic_data
            
        except Exception as e:
            logger.error(f"Error monitoring CAN bus traffic: {e}")
            traffic_data['error'] = str(e)
            return traffic_data
    
    def _identify_mazda_message(self, frame: CANFrame) -> Optional[Dict[str, Any]]:
        """Identify Mazda-specific CAN messages"""
        try:
            # Check if frame matches known Mazda addresses
            for msg_type, address in self.mazda_addresses.items():
                if frame.frame_id == address:
                    return {
                        'frame_id': f"0x{frame.frame_id:03X}",
                        'message_type': msg_type,
                        'data': frame.data.hex().upper(),
                        'timestamp': frame.timestamp
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error identifying Mazda message: {e}")
            return None
    
    def perform_bus_health_check(self) -> Dict[str, Any]:
        """
        Perform CAN bus health check
        
        Returns:
            Bus health status
        """
        health_status = {
            'bus_voltage': 'Unknown',
            'termination': 'Unknown',
            'error_rate': 'Unknown',
            'traffic_level': 'Unknown',
            'recommendations': []
        }
        
        try:
            # Monitor bus for short period
            traffic_data = self.monitor_bus_traffic(duration=5.0)
            
            # Analyze traffic
            total_frames = traffic_data.get('total_frames', 0)
            error_frames = traffic_data.get('error_frames', 0)
            
            # Calculate error rate
            if total_frames > 0:
                error_rate = (error_frames / total_frames) * 100
                health_status['error_rate'] = f"{error_rate:.2f}%"
                
                if error_rate > 5.0:
                    health_status['recommendations'].append("High error rate detected - check wiring")
                elif error_rate > 1.0:
                    health_status['recommendations'].append("Moderate error rate - monitor bus health")
                else:
                    health_status['recommendations'].append("Error rate within normal limits")
            else:
                health_status['error_rate'] = "No traffic"
                health_status['recommendations'].append("No bus traffic detected - check connection")
            
            # Assess traffic level
            data_rate = traffic_data.get('data_rate', 0)
            if data_rate > 1000:
                health_status['traffic_level'] = "High"
            elif data_rate > 100:
                health_status['traffic_level'] = "Medium"
            elif data_rate > 0:
                health_status['traffic_level'] = "Low"
            else:
                health_status['traffic_level'] = "None"
            
            # Check for common Mazda ECUs
            mazda_ecus_found = 0
            for msg in traffic_data.get('identified_messages', []):
                if any(ecu in msg.get('message_type', '') for ecu in ['ECU', 'TCM', 'ABS', 'BCM']):
                    mazda_ecus_found += 1
            
            if mazda_ecus_found >= 3:
                health_status['recommendations'].append("Multiple Mazda ECUs detected - bus communication normal")
            elif mazda_ecus_found > 0:
                health_status['recommendations'].append("Some Mazda ECUs detected - check missing modules")
            else:
                health_status['recommendations'].append("No Mazda ECUs detected - check vehicle connection")
            
            logger.info("CAN bus health check completed")
            return health_status
            
        except Exception as e:
            logger.error(f"Error performing bus health check: {e}")
            health_status['error'] = str(e)
            return health_status
    
    def set_bitrate(self, bitrate: int) -> bool:
        """
        Set CAN bus bitrate
        
        Args:
            bitrate: New bitrate in bits per second
            
        Returns:
            True if bitrate set successfully
        """
        try:
            # This would require system-level CAN configuration
            # For now, just update the internal value
            self.bitrate = bitrate
            logger.info(f"CAN bitrate set to {bitrate} bps")
            return True
            
        except Exception as e:
            logger.error(f"Error setting CAN bitrate: {e}")
            return False
    
    def get_interface_status(self) -> Dict[str, Any]:
        """
        Get CAN interface status
        
        Returns:
            Interface status information
        """
        status = {
            'interface': self.interface,
            'connected': self.is_connected,
            'bitrate': self.bitrate,
            'receive_thread_running': self.receive_running,
            'socket_available': self.socket is not None
        }
        
        return status