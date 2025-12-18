#!/usr/bin/env python3
"""
File Operations Utility - Comprehensive file handling for ROM files, maps, and configurations
Provides professional file management with validation and backup capabilities
"""

import os
import json
import shutil
import hashlib
import zipfile
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .logger import VersaLogger

class FileManager:
    """
    Professional file management for VersaTuner
    Handles ROM files, tuning maps, configurations, and backups
    """
    
    def __init__(self, base_directory: str = None):
        """
        Initialize File Manager
        
        Args:
            base_directory: Base directory for VersaTuner files
        """
        self.logger = VersaLogger(__name__)
        
        # Set base directory
        if base_directory:
            self.base_dir = base_directory
        else:
            self.base_dir = os.path.join(os.path.expanduser('~'), '.versatuner')
        
        # Create directory structure
        self._create_directory_structure()
    
    def _create_directory_structure(self):
        """Create VersaTuner directory structure"""
        directories = [
            'roms',
            'backups', 
            'maps',
            'tunes',
            'logs',
            'config',
            'exports'
        ]
        
        for directory in directories:
            dir_path = os.path.join(self.base_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
        
        self.logger.info(f"File structure created at: {self.base_dir}")
    
    def save_rom_file(self, rom_data: bytes, filename: str, 
                     metadata: Dict[str, Any] = None) -> str:
        """
        Save ROM file with metadata
        
        Args:
            rom_data: ROM data bytes
            filename: Output filename
            metadata: Optional metadata to save
            
        Returns:
            str: Path to saved file
        """
        # Ensure .bin extension
        if not filename.lower().endswith('.bin'):
            filename += '.bin'
        
        file_path = os.path.join(self.base_dir, 'roms', filename)
        
        try:
            # Save ROM data
            with open(file_path, 'wb') as f:
                f.write(rom_data)
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Save metadata
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'filename': filename,
                'file_size': len(rom_data),
                'file_hash': file_hash,
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            })
            
            meta_path = file_path + '.meta'
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"ROM file saved: {file_path} ({len(rom_data)} bytes)")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to save ROM file: {e}")
            raise
    
    def load_rom_file(self, filename: str) -> tuple[bytes, Dict[str, Any]]:
        """
        Load ROM file with metadata
        
        Args:
            filename: ROM filename to load
            
        Returns:
            tuple: (rom_data, metadata)
        """
        file_path = os.path.join(self.base_dir, 'roms', filename)
        meta_path = file_path + '.meta'
        
        try:
            # Load ROM data
            with open(file_path, 'rb') as f:
                rom_data = f.read()
            
            # Load metadata
            metadata = {}
            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
            
            # Verify file integrity
            current_hash = self._calculate_file_hash(file_path)
            if metadata.get('file_hash') != current_hash:
                self.logger.warning("ROM file hash mismatch - file may be corrupted")
            
            self.logger.info(f"ROM file loaded: {file_path} ({len(rom_data)} bytes)")
            return rom_data, metadata
            
        except Exception as e:
            self.logger.error(f"Failed to load ROM file: {e}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def create_backup(self, rom_data: bytes, backup_name: str = None) -> str:
        """
        Create ROM backup
        
        Args:
            rom_data: ROM data to backup
            backup_name: Optional backup name
            
        Returns:
            str: Path to backup file
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.bin"
        
        backup_path = os.path.join(self.base_dir, 'backups', backup_name)
        
        try:
            with open(backup_path, 'wb') as f:
                f.write(rom_data)
            
            # Create backup info
            backup_info = {
                'name': backup_name,
                'size': len(rom_data),
                'created_at': datetime.now().isoformat(),
                'hash': hashlib.sha256(rom_data).hexdigest()
            }
            
            info_path = backup_path + '.info'
            with open(info_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            self.logger.info(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Returns:
            List of backup information dictionaries
        """
        backup_dir = os.path.join(self.base_dir, 'backups')
        backups = []
        
        try:
            for filename in os.listdir(backup_dir):
                if filename.endswith('.bin'):
                    backup_path = os.path.join(backup_dir, filename)
                    info_path = backup_path + '.info'
                    
                    backup_info = {
                        'filename': filename,
                        'path': backup_path,
                        'size': os.path.getsize(backup_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(backup_path))
                    }
                    
                    # Load additional info if available
                    if os.path.exists(info_path):
                        with open(info_path, 'r') as f:
                            backup_info.update(json.load(f))
                    
                    backups.append(backup_info)
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_name: str) -> bytes:
        """
        Restore ROM from backup
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            bytes: ROM data from backup
        """
        backup_path = os.path.join(self.base_dir, 'backups', backup_name)
        
        try:
            with open(backup_path, 'rb') as f:
                rom_data = f.read()
            
            self.logger.info(f"Backup restored: {backup_name} ({len(rom_data)} bytes)")
            return rom_data
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            raise
    
    def save_tune_definition(self, tune_data: Dict[str, Any], tune_name: str) -> str:
        """
        Save tuning definition to file
        
        Args:
            tune_data: Tuning data dictionary
            tune_name: Name for the tune
            
        Returns:
            str: Path to saved tune file
        """
        if not tune_name.endswith('.json'):
            tune_name += '.json'
        
        tune_path = os.path.join(self.base_dir, 'tunes', tune_name)
        
        try:
            # Add metadata
            tune_data['metadata'] = {
                'name': tune_name.replace('.json', ''),
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'author': 'VersaTuner'
            }
            
            with open(tune_path, 'w') as f:
                json.dump(tune_data, f, indent=2)
            
            self.logger.info(f"Tune definition saved: {tune_path}")
            return tune_path
            
        except Exception as e:
            self.logger.error(f"Failed to save tune definition: {e}")
            raise
    
    def load_tune_definition(self, tune_name: str) -> Dict[str, Any]:
        """
        Load tuning definition from file
        
        Args:
            tune_name: Name of tune to load
            
        Returns:
            Dict containing tune data
        """
        if not tune_name.endswith('.json'):
            tune_name += '.json'
        
        tune_path = os.path.join(self.base_dir, 'tunes', tune_name)
        
        try:
            with open(tune_path, 'r') as f:
                tune_data = json.load(f)
            
            self.logger.info(f"Tune definition loaded: {tune_path}")
            return tune_data
            
        except Exception as e:
            self.logger.error(f"Failed to load tune definition: {e}")
            raise
    
    def list_tunes(self) -> List[Dict[str, Any]]:
        """
        List all available tunes
        
        Returns:
            List of tune information dictionaries
        """
        tune_dir = os.path.join(self.base_dir, 'tunes')
        tunes = []
        
        try:
            for filename in os.listdir(tune_dir):
                if filename.endswith('.json'):
                    tune_path = os.path.join(tune_dir, filename)
                    
                    try:
                        with open(tune_path, 'r') as f:
                            tune_data = json.load(f)
                        
                        tune_info = {
                            'filename': filename,
                            'path': tune_path,
                            'name': tune_data.get('metadata', {}).get('name', filename),
                            'created_at': tune_data.get('metadata', {}).get('created_at', 'Unknown'),
                            'size': os.path.getsize(tune_path)
                        }
                        
                        tunes.append(tune_info)
                        
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid tune file: {filename}")
            
            # Sort by name
            tunes.sort(key=lambda x: x['name'])
            
        except Exception as e:
            self.logger.error(f"Failed to list tunes: {e}")
        
        return tunes
    
    def export_tune_package(self, rom_data: bytes, tune_data: Dict[str, Any], 
                          export_name: str) -> str:
        """
        Export complete tune package (ROM + tune definition)
        
        Args:
            rom_data: Tuned ROM data
            tune_data: Tune definition data
            export_name: Name for export package
            
        Returns:
            str: Path to export package
        """
        if not export_name.endswith('.vtune'):
            export_name += '.vtune'
        
        export_path = os.path.join(self.base_dir, 'exports', export_name)
        
        try:
            # Create temporary directory for package contents
            temp_dir = os.path.join(self.base_dir, 'temp', export_name.replace('.vtune', ''))
            os.makedirs(temp_dir, exist_ok=True)
            
            # Save ROM file
            rom_filename = 'tuned_rom.bin'
            rom_path = os.path.join(temp_dir, rom_filename)
            with open(rom_path, 'wb') as f:
                f.write(rom_data)
            
            # Save tune definition
            tune_filename = 'tune_definition.json'
            tune_path = os.path.join(temp_dir, tune_filename)
            with open(tune_path, 'w') as f:
                json.dump(tune_data, f, indent=2)
            
            # Create package info
            package_info = {
                'package_name': export_name,
                'rom_file': rom_filename,
                'tune_file': tune_filename,
                'created_at': datetime.now().isoformat(),
                'rom_size': len(rom_data),
                'version': '1.0'
            }
            
            info_path = os.path.join(temp_dir, 'package_info.json')
            with open(info_path, 'w') as f:
                json.dump(package_info, f, indent=2)
            
            # Create ZIP package
            with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # Cleanup temporary directory
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"Tune package exported: {export_path}")
            return export_path
            
        except Exception as e:
            self.logger.error(f"Failed to export tune package: {e}")
            # Cleanup on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise
    
    def import_tune_package(self, package_path: str) -> tuple[bytes, Dict[str, Any]]:
        """
        Import tune package
        
        Args:
            package_path: Path to .vtune package file
            
        Returns:
            tuple: (rom_data, tune_data)
        """
        try:
            # Extract package
            temp_dir = os.path.join(self.base_dir, 'temp', 'import')
            os.makedirs(temp_dir, exist_ok=True)
            
            with zipfile.ZipFile(package_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Read package info
            info_path = os.path.join(temp_dir, 'package_info.json')
            with open(info_path, 'r') as f:
                package_info = json.load(f)
            
            # Load ROM data
            rom_path = os.path.join(temp_dir, package_info['rom_file'])
            with open(rom_path, 'rb') as f:
                rom_data = f.read()
            
            # Load tune definition
            tune_path = os.path.join(temp_dir, package_info['tune_file'])
            with open(tune_path, 'r') as f:
                tune_data = json.load(f)
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            self.logger.info(f"Tune package imported: {package_path}")
            return rom_data, tune_data
            
        except Exception as e:
            self.logger.error(f"Failed to import tune package: {e}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise
    
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage usage information
        
        Returns:
            Dict containing storage statistics
        """
        storage_info = {
            'base_directory': self.base_dir,
            'total_size': 0,
            'file_counts': {},
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            for category in ['roms', 'backups', 'tunes', 'maps', 'exports']:
                category_path = os.path.join(self.base_dir, category)
                category_size = 0
                file_count = 0
                
                for root, dirs, files in os.walk(category_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        category_size += os.path.getsize(file_path)
                        file_count += 1
                
                storage_info['file_counts'][category] = file_count
                storage_info['total_size'] += category_size
            
            # Convert sizes to human readable format
            storage_info['total_size_mb'] = storage_info['total_size'] / (1024 * 1024)
            
        except Exception as e:
            self.logger.error(f"Failed to get storage info: {e}")
        
        return storage_info
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """
        Clean up files older than specified days
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            int: Number of files removed
        """
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        removed_count = 0
        
        try:
            for category in ['backups', 'exports', 'logs']:
                category_path = os.path.join(self.base_dir, category)
                
                for root, dirs, files in os.walk(category_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            removed_count += 1
                            self.logger.info(f"Removed old file: {file_path}")
            
            self.logger.info(f"Cleanup completed: {removed_count} files removed")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
        
        return removed_count
