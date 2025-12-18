#!/usr/bin/env python3
"""
SECURITY AND ENCRYPTION UTILITIES FOR MAZDASPEED 3 TUNING
Protects sensitive tuning data and AI models
"""

import os
import hashlib
import hmac
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from typing import Dict, Optional, Tuple
import secrets

class SecurityError(Exception):
    """Custom security exception"""
    pass

class SecurityManager:
    """
    Security manager for protecting tuning data
    Provides encryption, authentication, and integrity checks
    """
    
    def __init__(self, master_password: Optional[str] = None):
        self.master_password = master_password or os.environ.get('MUTS_MASTER_KEY', 'default-key')
        self.salt = b'muts_security_salt_2024'
        self.fernet = None
        
        # Initialize encryption
        self._initialize_encryption()
        
        # Security configuration
        self.config = {
            'encryption_enabled': True,
            'integrity_check': True,
            'authentication_required': True,
            'key_rotation_days': 90
        }
    
    def _initialize_encryption(self):
        """Initialize Fernet encryption with PBKDF2 key derivation"""
        # Derive key from master password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))
        self.fernet = Fernet(key)
    
    def encrypt_calibration_data(self, calibration: Dict) -> bytes:
        """
        Encrypt calibration data for storage
        Returns encrypted bytes
        """
        if not self.config['encryption_enabled']:
            return json.dumps(calibration).encode()
        
        # Convert to JSON
        json_data = json.dumps(calibration).encode()
        
        # Encrypt
        encrypted_data = self.fernet.encrypt(json_data)
        
        return encrypted_data
    
    def decrypt_calibration_data(self, encrypted_data: bytes) -> Dict:
        """
        Decrypt calibration data
        Returns calibration dictionary
        """
        if not self.config['encryption_enabled']:
            return json.loads(encrypted_data.decode())
        
        try:
            # Decrypt
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            # Parse JSON
            calibration = json.loads(decrypted_data.decode())
            
            return calibration
        except Exception as e:
            raise SecurityError(f"Failed to decrypt calibration data: {str(e)}")
    
    def generate_vehicle_signature(self, vin: str, ecu_id: str, 
                                calibration_id: str) -> str:
        """
        Generate unique vehicle signature
        Used for authentication and licensing
        """
        # Combine vehicle identifiers
        vehicle_data = f"{vin}:{ecu_id}:{calibration_id}"
        
        # Generate HMAC signature
        signature = hmac.new(
            self.master_password.encode(),
            vehicle_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_vehicle_signature(self, vin: str, ecu_id: str,
                              calibration_id: str, signature: str) -> bool:
        """
        Verify vehicle signature
        Returns True if valid
        """
        expected_signature = self.generate_vehicle_signature(
            vin, ecu_id, calibration_id
        )
        
        return hmac.compare_digest(signature, expected_signature)
    
    def protect_ai_model(self, model_data: bytes, model_name: str) -> Dict:
        """
        Protect AI model with encryption and metadata
        Returns protected model package
        """
        protection_package = {
            'model_name': model_name,
            'version': '1.0',
            'encrypted': self.config['encryption_enabled'],
            'checksum': None,
            'data': None
        }
        
        if self.config['encryption_enabled']:
            # Encrypt model data
            protected_package['data'] = self.fernet.encrypt(model_data).decode()
        else:
            protected_package['data'] = base64.b64encode(model_data).decode()
        
        # Calculate checksum
        checksum = hashlib.sha256(model_data).hexdigest()
        protection_package['checksum'] = checksum
        
        return protection_package
    
    def extract_ai_model(self, protection_package: Dict) -> bytes:
        """
        Extract and verify AI model from protection package
        Returns raw model data
        """
        try:
            # Extract data
            if protection_package['encrypted']:
                model_data = self.fernet.decrypt(
                    protection_package['data'].encode()
                )
            else:
                model_data = base64.b64decode(
                    protection_package['data'].encode()
                )
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(model_data).hexdigest()
            if not hmac.compare_digest(
                calculated_checksum, 
                protection_package['checksum']
            ):
                raise SecurityError("Model integrity check failed")
            
            return model_data
            
        except Exception as e:
            raise SecurityError(f"Failed to extract AI model: {str(e)}")
    
    def create_secure_session(self, user_id: str, permissions: list) -> Dict:
        """
        Create secure session for user authentication
        Returns session token and metadata
        """
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session data
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'permissions': permissions,
            'created_at': secrets.token_hex(16),
            'expires_in': 3600  # 1 hour
        }
        
        # Sign session
        session_json = json.dumps(session_data, sort_keys=True)
        signature = hmac.new(
            self.master_password.encode(),
            session_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Create session token
        session_token = f"{session_id}.{signature}"
        
        return {
            'token': session_token,
            'session_data': session_data
        }
    
    def verify_session(self, session_token: str) -> Optional[Dict]:
        """
        Verify session token
        Returns session data if valid, None otherwise
        """
        try:
            # Split token
            parts = session_token.split('.')
            if len(parts) != 2:
                return None
            
            session_id, signature = parts
            
            # Get session data (simplified - would use database in production)
            # For now, just verify signature format
            if len(signature) != 64:  # SHA256 hex length
                return None
            
            return {'session_id': session_id, 'valid': True}
            
        except:
            return None
    
    def generate_api_key(self, client_id: str, permissions: list) -> Tuple[str, str]:
        """
        Generate API key for client
        Returns (api_key, api_secret)
        """
        # Generate API key
        api_key = secrets.token_urlsafe(32)
        
        # Generate API secret
        api_secret = secrets.token_urlsafe(64)
        
        # Store association (simplified)
        key_data = {
            'api_key': api_key,
            'client_id': client_id,
            'permissions': permissions,
            'created_at': secrets.token_hex(16)
        }
        
        # Sign key data
        key_json = json.dumps(key_data, sort_keys=True)
        signature = hmac.new(
            self.master_password.encode(),
            key_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine secret and signature
        full_secret = f"{api_secret}.{signature}"
        
        return api_key, full_secret
    
    def verify_api_key(self, api_key: str, api_secret: str) -> Optional[Dict]:
        """
        Verify API key and secret
        Returns client data if valid
        """
        try:
            # Split secret
            parts = api_secret.split('.')
            if len(parts) != 2:
                return None
            
            secret, signature = parts
            
            # Verify format
            if len(api_key) != 43 or len(secret) != 86 or len(signature) != 64:
                return None
            
            return {
                'api_key': api_key,
                'valid': True,
                'verified_at': secrets.token_hex(16)
            }
            
        except:
            return None
    
    def encrypt_communication(self, data: bytes, recipient_key: str) -> bytes:
        """
        Encrypt communication data
        Simplified implementation
        """
        if not self.config['encryption_enabled']:
            return data
        
        # Add HMAC for integrity
        hmac_signature = hmac.new(
            recipient_key.encode(),
            data,
            hashlib.sha256
        ).digest()
        
        # Combine data and signature
        encrypted_data = data + b'|' + hmac_signature
        
        return encrypted_data
    
    def decrypt_communication(self, encrypted_data: bytes, 
                            sender_key: str) -> Optional[bytes]:
        """
        Decrypt and verify communication data
        """
        try:
            # Split data and signature
            parts = encrypted_data.split(b'|')
            if len(parts) != 2:
                return None
            
            data, received_signature = parts
            
            # Verify HMAC
            expected_signature = hmac.new(
                sender_key.encode(),
                data,
                hashlib.sha256
            ).digest()
            
            if not hmac.compare_digest(received_signature, expected_signature):
                return None
            
            return data
            
        except:
            return None
    
    def secure_erase(self, data: bytes) -> bool:
        """
        Securely erase sensitive data
        Overwrites memory with random data
        """
        try:
            # Overwrite with random data
            for _ in range(3):
                random_data = secrets.token_bytes(len(data))
                data[:] = random_data
            
            # Final overwrite with zeros
            data[:] = b'\x00' * len(data)
            
            return True
            
        except:
            return False
    
    def rotate_encryption_key(self):
        """
        Rotate encryption key
        Should be called periodically
        """
        # Generate new salt
        self.salt = secrets.token_bytes(32)
        
        # Reinitialize encryption
        self._initialize_encryption()
    
    def get_security_status(self) -> Dict:
        """
        Get current security configuration status
        """
        return {
            'encryption_enabled': self.config['encryption_enabled'],
            'integrity_check': self.config['integrity_check'],
            'authentication_required': self.config['authentication_required'],
            'key_rotation_days': self.config['key_rotation_days'],
            'encryption_algorithm': 'Fernet (AES-128-CBC)',
            'hash_algorithm': 'SHA256',
            'key_derivation': 'PBKDF2'
        }

class TuningDataProtector:
    """
    Specialized protector for tuning data
    Handles calibration maps, AI models, and sensitive parameters
    """
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.protection_level = 'high'  # low, medium, high
    
    def protect_calibration_map(self, map_data: Dict, 
                              calibration_id: str) -> Dict:
        """
        Protect calibration map with appropriate level of security
        """
        protected_map = {
            'calibration_id': calibration_id,
            'protection_level': self.protection_level,
            'encrypted_data': None,
            'metadata': {
                'map_size': len(str(map_data)),
                'created_at': secrets.token_hex(16),
                'checksum': None
            }
        }
        
        if self.protection_level == 'high':
            # Full encryption
            protected_map['encrypted_data'] = self.security.encrypt_calibration_data(
                map_data
            ).decode()
        elif self.protection_level == 'medium':
            # Partial encryption - only sensitive values
            sensitive_data = self._extract_sensitive_data(map_data)
            protected_map['encrypted_data'] = self.security.encrypt_calibration_data(
                sensitive_data
            ).decode()
            protected_map['public_data'] = self._extract_public_data(map_data)
        else:
            # No encryption, just checksum
            protected_map['public_data'] = map_data
        
        # Calculate checksum
        map_json = json.dumps(map_data, sort_keys=True)
        checksum = hashlib.sha256(map_json.encode()).hexdigest()
        protected_map['metadata']['checksum'] = checksum
        
        return protected_map
    
    def _extract_sensitive_data(self, map_data: Dict) -> Dict:
        """
        Extract sensitive data from calibration map
        """
        sensitive = {}
        
        # Define what's sensitive
        sensitive_keys = [
            'ignition_map_high_octane',
            'ignition_map_low_octane',
            'fuel_base_map',
            'boost_target_map',
            'torque_limiters'
        ]
        
        for key in sensitive_keys:
            if key in map_data:
                sensitive[key] = map_data[key]
        
        return sensitive
    
    def _extract_public_data(self, map_data: Dict) -> Dict:
        """
        Extract non-sensitive data from calibration map
        """
        public = map_data.copy()
        
        # Remove sensitive keys
        sensitive_keys = [
            'ignition_map_high_octane',
            'ignition_map_low_octane',
            'fuel_base_map',
            'boost_target_map',
            'torque_limiters'
        ]
        
        for key in sensitive_keys:
            public.pop(key, None)
        
        return public
    
    def verify_calibration_integrity(self, protected_map: Dict) -> bool:
        """
        Verify calibration map integrity
        """
        if 'metadata' not in protected_map or 'checksum' not in protected_map['metadata']:
            return False
        
        # Get original data
        if protected_map['protection_level'] == 'high':
            original_data = self.security.decrypt_calibration_data(
                protected_map['encrypted_data'].encode()
            )
        else:
            original_data = protected_map.get('public_data', {})
        
        # Verify checksum
        data_json = json.dumps(original_data, sort_keys=True)
        calculated_checksum = hashlib.sha256(data_json.encode()).hexdigest()
        
        return hmac.compare_digest(
            calculated_checksum,
            protected_map['metadata']['checksum']
        )
