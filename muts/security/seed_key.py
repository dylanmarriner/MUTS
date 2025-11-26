"""
Mazda ECU seed/key helpers for diagnostic security access
"""

import hashlib
import logging
from typing import Dict, Callable, Optional
from enum import IntEnum
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class MazdaECUType(IntEnum):
    ENGINE_ECU = 0x01
    TRANSMISSION = 0x02
    IMMOBILIZER = 0x03
    BODY_CONTROL = 0x04
    ABS = 0x05
    AIRBAG = 0x06
    INSTRUMENT_CLUSTER = 0x07
    GATEWAY = 0x08


class MazdaSeedKeyDatabase:
    """
    Seed-key helper database for Mazda ECUs
    """

    def __init__(self):
        self.algorithm_database = self._initialize_algorithm_database()
        self.ecu_database = self._initialize_ecu_database()

    def _initialize_algorithm_database(self) -> Dict[str, Callable]:
        return {
            "ALG_27_STANDARD": self._algorithm_27_standard,
            "ENGINE_ECU_2011": self._algorithm_engine_ecu_2011,
            "IMMOBILIZER_2011": self._algorithm_immobilizer_2011,
        }

    def _initialize_ecu_database(self) -> Dict[MazdaECUType, Dict[str, any]]:
        return {
            MazdaECUType.ENGINE_ECU: {
                "algorithm": "ENGINE_ECU_2011",
                "seed_length": 4,
                "key_length": 4,
                "security_levels": [1, 2, 3, 4, 5, 6],
                "vin_required": False
            },
            MazdaECUType.IMMOBILIZER: {
                "algorithm": "IMMOBILIZER_2011",
                "seed_length": 8,
                "key_length": 8,
                "security_levels": [5],
                "vin_required": True
            },
        }

    def calculate_key(self, seed: bytes, algorithm_name: str,
                      vin: Optional[str] = None, security_level: int = 1) -> Optional[bytes]:
        try:
            if algorithm_name not in self.algorithm_database:
                logger.error(f"Unknown algorithm: {algorithm_name}")
                return None
            algorithm = self.algorithm_database[algorithm_name]
            key = algorithm(seed, vin, security_level)
            if key:
                logger.debug(f"Calculated key using {algorithm_name}: {key.hex().upper()}")
            else:
                logger.error(f"Algorithm {algorithm_name} returned no key")
            return key
        except Exception as e:
            logger.error(f"Error calculating key with {algorithm_name}: {e}")
            return None

    def _algorithm_27_standard(self, seed: bytes, vin: Optional[str] = None, security_level: int = 1) -> bytes:
        if len(seed) != 4:
            raise ValueError("Standard algorithm requires 4-byte seed")
        key = bytearray(4)
        for i in range(4):
            temp = seed[i] ^ 0x73
            temp = (temp + i) & 0xFF
            temp = temp ^ 0xA9
            key[i] = (temp + 0x1F) & 0xFF
        return bytes(key)

    def _algorithm_engine_ecu_2011(self, seed: bytes, vin: Optional[str] = None, security_level: int = 1) -> bytes:
        if len(seed) != 4:
            raise ValueError("Engine ECU algorithm requires 4-byte seed")
        key = bytearray(4)
        level_factor = {
            1: 0x10,
            2: 0x20,
            3: 0x30,
            4: 0x40,
            5: 0x50,
            6: 0x60
        }.get(security_level, 0x10)
        for i in range(4):
            temp = (seed[i] ^ 0x5A) + level_factor
            temp = ((temp << 4) | (temp >> 4)) & 0xFF
            temp = temp ^ [0x37, 0x92, 0x64, 0xA8][i]
            temp = (temp + i * 2) & 0xFF
            key[i] = ~temp & 0xFF
        return bytes(key)

    def _algorithm_immobilizer_2011(self, seed: bytes, vin: Optional[str] = None, security_level: int = 1) -> bytes:
        if len(seed) != 8:
            raise ValueError("Immobilizer algorithm requires 8-byte seed")
        if not vin:
            raise ValueError("Immobilizer algorithm requires VIN")
        vehicle_key = self._derive_immobilizer_key(vin)
        des_key = vehicle_key[:24]
        cipher = Cipher(algorithms.TripleDES(des_key), modes.ECB(), default_backend())
        encryptor = cipher.encryptor()
        return encryptor.update(seed) + encryptor.finalize()

    def _derive_immobilizer_key(self, vin: str) -> bytes:
        vin_bytes = vin.encode('ascii')
        key = hashlib.md5(vin_bytes).digest()
        key = hashlib.sha256(key + b'mazda_immobilizer_salt_1').digest()
        key = hashlib.sha256(key + b'mazda_immobilizer_salt_2').digest()
        return key[:24]


def bypass_security():
    """
    Demonstrates calculating keys for dealer-level access.
    """
    logging.info("Attempting to bypass ECU security...")
    seed_key_db = MazdaSeedKeyDatabase()
    ecu_info = seed_key_db.ecu_database.get(MazdaECUType.ENGINE_ECU)

    if ecu_info:
        algorithm_name = ecu_info["algorithm"]
        seed_length = ecu_info["seed_length"]
        seed = b'\xDE\xAD\xBE\xEF'[:seed_length]
        logging.info(f"Calculating key for ENGINE_ECU using {algorithm_name}")
        key = seed_key_db.calculate_key(seed, algorithm_name)
        if key:
            logging.info(f"Successfully calculated key: {key.hex().upper()}")
        else:
            logging.error("Failed to calculate key.")

    ecu_info = seed_key_db.ecu_database.get(MazdaECUType.IMMOBILIZER)
    if ecu_info:
        algorithm_name = ecu_info["algorithm"]
        seed_length = ecu_info["seed_length"]
        seed = b'\xDE\xAD\xBE\xEF\xDE\xAD\xBE\xEF'[:seed_length]
        vin = "JM1BK123456789012"
        logging.info(f"Calculating key for IMMOBILIZER using {algorithm_name}")
        key = seed_key_db.calculate_key(seed, algorithm_name, vin=vin)
        if key:
            logging.info(f"Successfully calculated key for immobilizer: {key.hex().upper()}")
        else:
            logging.error("Failed to calculate key for immobilizer.")


__all__ = ["MazdaECUType", "MazdaSeedKeyDatabase", "bypass_security"]
