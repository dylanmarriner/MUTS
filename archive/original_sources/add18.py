#!/usr/bin/env python3
"""
SECURITY AND ENCRYPTION UTILITIES
Protects tuning data and prevents unauthorized access
"""

import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os

class SecurityManager:
    """
    COMPLETE SECURITY MANAGEMENT FOR TUNING DATA
    Encrypts calibration files, protects AI models, and secures communication
    """
    
    def __init__(self, master_key: str = None):
        self.master_key = master_key or self._generate_master_key()
        self.fernet = Fernet(self._derive_encryption_key(self.master_key))
        
        # Security parameters
        self.key_derivation_iterations = 100000
        self.token_expiry_hours = 24
        
    def _generate_master_key(self) -> str:
        """Generate cryptographically secure master key"""
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def _derive_encryption_key(self, password: str) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        salt = b'mazdaspeed3_tuning_salt_2024'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.key_derivation_iterations,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_calibration_data(self, calibration_data: dict) -> str:
        """
        Encrypt ECU calibration data for secure storage
        """
        try:
            # Convert to JSON string
            import json
            data_str = json.dumps(calibration_data, separators=(',', ':'))
            
            # Encrypt data
            encrypted_data = self.fernet.encrypt(data_str.encode())
            
            # Add integrity check
            integrity_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            # Package encrypted data with metadata
            encrypted_package = {
                'data': base64.urlsafe_b64encode(encrypted_data).decode(),
                'integrity_hash': integrity_hash,
                'timestamp': str(int(time.time())),
                'version': '1.0'
            }
            
            return base64.urlsafe_b64encode(json.dumps(encrypted_package).encode()).decode()
            
        except Exception as e:
            raise SecurityError(f"Calibration encryption failed: {e}")
    
    def decrypt_calibration_data(self, encrypted_package: str) -> dict:
        """
        Decrypt ECU calibration data with integrity verification
        """
        try:
            # Unpackage encrypted data
            package_str = base64.urlsafe_b64decode(encrypted_package.encode()).decode()
            package = json.loads(package_str)
            
            # Decrypt data
            encrypted_data = base64.urlsafe_b64decode(package['data'].encode())
            decrypted_data = self.fernet.decrypt(encrypted_data).decode()
            
            # Verify integrity
            integrity_hash = hashlib.sha256(decrypted_data.encode()).hexdigest()
            if integrity_hash != package['integrity_hash']:
                raise SecurityError("Data integrity check failed")
            
            # Parse back to dictionary
            calibration_data = json.loads(decrypted_data)
            
            return calibration_data
            
        except Exception as e:
            raise SecurityError(f"Calibration decryption failed: {e}")
    
    def generate_vehicle_signature(self, vin: str, calibration_id: str) -> str:
        """
        Generate unique vehicle signature for tuning file validation
        Prevents tuning files from being used on unauthorized vehicles
        """
        try:
            # Create signature payload
            payload = f"{vin}:{calibration_id}:{int(time.time())}"
            
            # Generate HMAC signature
            signature = hmac.new(
                self.master_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Package signature
            signature_package = {
                'vin': vin,
                'calibration_id': calibration_id,
                'signature': signature,
                'timestamp': int(time.time())
            }
            
            return base64.urlsafe_b64encode(json.dumps(signature_package).encode()).decode()
            
        except Exception as e:
            raise SecurityError(f"Signature generation failed: {e}")
    
    def verify_vehicle_signature(self, signature_data: str, vin: str, calibration_id: str) -> bool:
        """
        Verify vehicle signature for tuning file authorization
        """
        try:
            # Decode signature package
            package_str = base64.urlsafe_b64decode(signature_data.encode()).decode()
            package = json.loads(package_str)
            
            # Check expiry (24 hours)
            current_time = int(time.time())
            if current_time - package['timestamp'] > self.token_expiry_hours * 3600:
                return False
            
            # Verify VIN and calibration ID match
            if package['vin'] != vin or package['calibration_id'] != calibration_id:
                return False
            
            # Regenerate and verify signature
            payload = f"{vin}:{calibration_id}:{package['timestamp']}"
            expected_signature = hmac.new(
                self.master_key.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(package['signature'], expected_signature)
            
        except Exception:
            return False
    
    def protect_ai_model(self, model_data: bytes) -> bytes:
        """
        Encrypt AI model files to protect intellectual property
        """
        try:
            # Generate unique IV for this model
            iv = os.urandom(16)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self._derive_encryption_key(self.master_key)[:32]),
                modes.CTR(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt model data
            encrypted_model = encryptor.update(model_data) + encryptor.finalize()
            
            # Package with IV
            protected_package = iv + encrypted_model
            
            return protected_package
            
        except Exception as e:
            raise SecurityError(f"AI model protection failed: {e}")
    
    def unprotect_ai_model(self, protected_data: bytes) -> bytes:
        """
        Decrypt AI model files
        """
        try:
            # Extract IV and encrypted data
            iv = protected_data[:16]
            encrypted_model = protected_data[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self._derive_encryption_key(self.master_key)[:32]),
                modes.CTR(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt model data
            model_data = decryptor.update(encrypted_model) + decryptor.finalize()
            
            return model_data
            
        except Exception as e:
            raise SecurityError(f"AI model unprotection failed: {e}")
    
    def secure_communication_channel(self, data: dict, session_key: str) -> str:
        """
        Secure data for transmission over communication channels
        """
        try:
            # Convert to JSON
            data_str = json.dumps(data, separators=(',', ':'))
            
            # Generate session-specific key
            session_fernet = Fernet(self._derive_encryption_key(session_key))
            
            # Encrypt data
            encrypted_data = session_fernet.encrypt(data_str.encode())
            
            # Add session metadata
            secure_package = {
                'session_id': hashlib.sha256(session_key.encode()).hexdigest()[:16],
                'data': base64.urlsafe_b64encode(encrypted_data).decode(),
                'timestamp': int(time.time())
            }
            
            return base64.urlsafe_b64encode(json.dumps(secure_package).encode()).decode()
            
        except Exception as e:
            raise SecurityError(f"Communication security failed: {e}")

class SecurityError(Exception):
    """Custom security exception"""
    pass

# Global security instance
security_manager = SecurityManager()