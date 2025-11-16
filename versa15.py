#!/usr/bin/env python3
"""
Compression Utility - Data compression and decompression for ROM files and logs
Provides efficient storage and transmission of large binary data
"""

import zlib
import lzma
import bz2
import base64
from typing import Optional, Union
from ..utils.logger import VersaLogger

class CompressionManager:
    """
    Data compression manager for VersaTuner
    Supports multiple compression algorithms for different use cases
    """
    
    def __init__(self):
        self.logger = VersaLogger(__name__)
    
    def compress_data(self, data: bytes, method: str = 'zlib', 
                     level: int = 6) -> bytes:
        """
        Compress data using specified method
        
        Args:
            data: Data to compress
            method: Compression method ('zlib', 'lzma', 'bz2')
            level: Compression level (1-9)
            
        Returns:
            bytes: Compressed data
        """
        try:
            if method == 'zlib':
                compressed = zlib.compress(data, level=level)
            elif method == 'lzma':
                compressed = lzma.compress(data, preset=level)
            elif method == 'bz2':
                compressed = bz2.compress(data, compresslevel=level)
            else:
                raise ValueError(f"Unknown compression method: {method}")
            
            compression_ratio = len(compressed) / len(data) if data else 0
            self.logger.debug(f"Data compressed: {len(data)} -> {len(compressed)} bytes "
                            f"(ratio: {compression_ratio:.2f})")
            
            return compressed
            
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            raise
    
    def decompress_data(self, compressed_data: bytes, method: str = 'zlib') -> bytes:
        """
        Decompress data
        
        Args:
            compressed_data: Compressed data
            method: Compression method used
            
        Returns:
            bytes: Decompressed data
        """
        try:
            if method == 'zlib':
                data = zlib.decompress(compressed_data)
            elif method == 'lzma':
                data = lzma.decompress(compressed_data)
            elif method == 'bz2':
                data = bz2.decompress(compressed_data)
            else:
                raise ValueError(f"Unknown compression method: {method}")
            
            self.logger.debug(f"Data decompressed: {len(compressed_data)} -> {len(data)} bytes")
            return data
            
        except Exception as e:
            self.logger.error(f"Decompression failed: {e}")
            raise
    
    def compress_and_encode(self, data: bytes, method: str = 'zlib') -> str:
        """
        Compress data and encode as base64 string
        
        Args:
            data: Data to compress and encode
            method: Compression method
            
        Returns:
            str: Base64 encoded compressed data
        """
        compressed = self.compress_data(data, method)
        encoded = base64.b64encode(compressed).decode('ascii')
        return encoded
    
    def decode_and_decompress(self, encoded_data: str, method: str = 'zlib') -> bytes:
        """
        Decode base64 string and decompress data
        
        Args:
            encoded_data: Base64 encoded compressed data
            method: Compression method used
            
        Returns:
            bytes: Decompressed data
        """
        compressed = base64.b64decode(encoded_data.encode('ascii'))
        data = self.decompress_data(compressed, method)
        return data
    
    def optimize_rom_storage(self, rom_data: bytes) -> bytes:
        """
        Optimize ROM data for storage using best compression method
        
        Args:
            rom_data: ROM data to optimize
            
        Returns:
            bytes: Optimized ROM data
        """
        self.logger.info("Optimizing ROM data for storage")
        
        # Try different compression methods
        methods = ['lzma', 'zlib', 'bz2']
        best_compressed = rom_data
        best_method = 'none'
        best_ratio = 1.0
        
        for method in methods:
            try:
                compressed = self.compress_data(rom_data, method, level=9)
                ratio = len(compressed) / len(rom_data)
                
                if ratio < best_ratio:
                    best_compressed = compressed
                    best_method = method
                    best_ratio = ratio
                    
            except Exception as e:
                self.logger.warning(f"Compression method {method} failed: {e}")
        
        self.logger.info(f"Best compression: {best_method} (ratio: {best_ratio:.3f})")
        
        # Add header indicating compression method
        header = f"VTCOMP:{best_method}:".encode('ascii')
        return header + best_compressed
    
    def restore_rom_data(self, optimized_data: bytes) -> bytes:
        """
        Restore ROM data from optimized storage format
        
        Args:
            optimized_data: Optimized ROM data
            
        Returns:
            bytes: Original ROM data
        """
        # Check if data is compressed
        if optimized_data.startswith(b"VTCOMP:"):
            # Extract compression method
            header_end = optimized_data.find(b':', 7)  # Find second colon
            if header_end == -1:
                raise ValueError("Invalid compressed data format")
            
            method = optimized_data[7:header_end].decode('ascii')
            compressed_data = optimized_data[header_end + 1:]
            
            self.logger.info(f"Decompressing ROM data (method: {method})")
            return self.decompress_data(compressed_data, method)
        else:
            # Data is not compressed
            return optimized_data
    
    def create_differential_patch(self, original_data: bytes, 
                                modified_data: bytes) -> bytes:
        """
        Create differential patch between original and modified data
        
        Args:
            original_data: Original data
            modified_data: Modified data
            
        Returns:
            bytes: Differential patch data
        """
        if len(original_data) != len(modified_data):
            raise ValueError("Data lengths must be equal for differential patching")
        
        # Create XOR diff
        diff = bytearray()
        for i in range(len(original_data)):
            diff.append(original_data[i] ^ modified_data[i])
        
        # Compress the diff (it should be highly compressible)
        compressed_diff = self.compress_data(bytes(diff), 'zlib', level=9)
        
        self.logger.info(f"Created differential patch: {len(compressed_diff)} bytes")
        return compressed_diff
    
    def apply_differential_patch(self, original_data: bytes, 
                               patch_data: bytes) -> bytes:
        """
        Apply differential patch to original data
        
        Args:
            original_data: Original data
            patch_data: Differential patch data
            
        Returns:
            bytes: Modified data
        """
        # Decompress patch
        diff = self.decompress_data(patch_data, 'zlib')
        
        if len(diff) != len(original_data):
            raise ValueError("Patch size doesn't match original data size")
        
        # Apply XOR diff
        modified = bytearray()
        for i in range(len(original_data)):
            modified.append(original_data[i] ^ diff[i])
        
        self.logger.info("Applied differential patch successfully")
        return bytes(modified)