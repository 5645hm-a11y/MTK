"""
Partition Extractor Module
Extracts firmware partitions from connected MTK device
"""

import os
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import struct
import hashlib


@dataclass
class PartitionInfo:
    """Information about a firmware partition"""
    name: str
    size: int
    offset: int
    type: str
    file_path: Optional[str] = None
    is_image: bool = False
    linear_start_addr: int = 0
    partition_size: int = 0


class PartitionExtractor:
    """Extract partitions from MTK devices"""
    
    def __init__(self, device_interface, config):
        self.device = device_interface
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.partitions: List[PartitionInfo] = []
        self.last_failed_partitions: Dict[str, str] = {}
        
    def read_partition_table(self) -> List[PartitionInfo]:
        """
        Read partition table from device
        For MTK devices, this reads the GPT or PMT (Partition Management Table)
        """
        self.logger.info("Reading partition table from device...")
        
        # Common MTK partitions as fallback
        common_partitions = self.config.get('partitions.common', [])
        build_required = self.config.get('partitions.build_required', [])

        # Build unified fallback list so critical partitions (e.g., super) are not missed.
        ordered_candidates = []
        for part in common_partitions + build_required:
            name = str(part).strip()
            if name and name not in ordered_candidates:
                ordered_candidates.append(name)
        
        # TODO: Implement actual partition table reading
        # This would involve reading GPT or PMT from the device
        
        # For now, create placeholder partition info
        self.partitions = []
        offset = 0
        
        for idx, name in enumerate(ordered_candidates):
            size = self._estimate_partition_size(name)
            
            partition = PartitionInfo(
                name=name,
                size=size,
                offset=offset,
                type='ext4' if name in ['system', 'vendor', 'userdata'] else 'raw',
                linear_start_addr=offset,
                partition_size=size
            )
            
            self.partitions.append(partition)
            offset += size

        self.logger.info(f"Fallback partition table source size: common={len(common_partitions)}, build_required={len(build_required)}, merged={len(ordered_candidates)}")
        
        self.logger.info(f"Found {len(self.partitions)} partitions")
        return self.partitions
    
    def _estimate_partition_size(self, partition_name: str) -> int:
        """Estimate partition size based on common values"""
        sizes = {
            'preloader': 256 * 1024,      # 256KB
            'lk': 512 * 1024,             # 512KB
            'lk2': 512 * 1024,            # 512KB
            'boot': 16 * 1024 * 1024,     # 16MB
            'recovery': 16 * 1024 * 1024, # 16MB
            'vendor_boot': 64 * 1024 * 1024, # 64MB
            'system': 2048 * 1024 * 1024, # 2GB
            'vendor': 512 * 1024 * 1024,  # 512MB
            'product': 1024 * 1024 * 1024, # 1GB
            'odm': 512 * 1024 * 1024,     # 512MB
            'super': 6144 * 1024 * 1024,  # 6GB
            'userdata': 4096 * 1024 * 1024, # 4GB
            'cache': 256 * 1024 * 1024,   # 256MB
            'nvram': 5 * 1024 * 1024,     # 5MB
            'logo': 8 * 1024 * 1024,      # 8MB
            'secro': 6 * 1024 * 1024,     # 6MB
            'vbmeta': 4 * 1024 * 1024,    # 4MB
            'vbmeta_system': 4 * 1024 * 1024, # 4MB
            'vbmeta_vendor': 4 * 1024 * 1024, # 4MB
            'dtbo': 32 * 1024 * 1024,     # 32MB
            'tee1': 4 * 1024 * 1024,      # 4MB
            'tee2': 4 * 1024 * 1024,      # 4MB
        }
        return sizes.get(partition_name, 128 * 1024 * 1024)  # Default 128MB

    def _is_required_for_build(self, partition: PartitionInfo) -> bool:
        """Return True when partition is required for rebuilding firmware for same device."""
        name = partition.name.lower()

        config_required = self.config.get('partitions.build_required', None)
        config_excluded = self.config.get('partitions.build_excluded', None)

        if isinstance(config_excluded, list) and config_excluded:
            excluded_from_config = {str(x).lower() for x in config_excluded}
            if name in excluded_from_config:
                return False

        if isinstance(config_required, list) and config_required:
            required_from_config = {str(x).lower() for x in config_required}
            # Keep flexible matching for names like system_a/vendor_b.
            return name in required_from_config or any(name.startswith(r + '_') for r in required_from_config)

        # Explicitly excluded partitions (user data/calibration/runtime data).
        excluded = {
            'userdata', 'cache', 'metadata', 'persist',
            'nvram', 'nvdata', 'protect1', 'protect2',
            'frp', 'otp', 'expdb', 'para'
        }

        # Core firmware partitions needed to rebuild/flash system image set.
        required_exact = {
            'preloader', 'lk', 'lk2', 'boot', 'recovery', 'vendor_boot',
            'vbmeta', 'vbmeta_system', 'vbmeta_vendor',
            'dtbo', 'tee1', 'tee2', 'logo', 'secro',
            'system', 'vendor', 'product', 'odm', 'super'
        }

        required_prefixes = (
            'system', 'vendor', 'product', 'odm', 'super',
            'boot', 'recovery', 'vbmeta', 'dtbo'
        )

        if name in excluded:
            return False

        if name in required_exact:
            return True

        return name.startswith(required_prefixes)

    def estimate_required_extraction_size(self, partitions: Optional[List[PartitionInfo]] = None) -> int:
        """Estimate bytes required to extract all required-for-build partitions."""
        source = partitions if partitions is not None else self.partitions
        if not source:
            source = self.read_partition_table()
        return sum(p.size for p in source if self._is_required_for_build(p))

    def has_enough_output_space(self, output_dir: Path, required_bytes: int, safety_ratio: float = 1.05) -> tuple[bool, int]:
        """Check if output filesystem has enough free bytes with safety margin."""
        output_dir.mkdir(parents=True, exist_ok=True)
        free_bytes = shutil.disk_usage(output_dir).free
        needed = int(required_bytes * safety_ratio)
        return free_bytes >= needed, free_bytes
    
    def extract_partition(self, partition: PartitionInfo, 
                         output_dir: Path,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """
        Extract a single partition to file
        
        Args:
            partition: Partition to extract
            output_dir: Directory to save partition image
            progress_callback: Optional callback for progress updates (current, total)
        
        Returns:
            Path to extracted partition file
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{partition.name}.img"
        
        self.logger.info(f"Extracting partition '{partition.name}' to {output_file}")
        
        chunk_size = 1024 * 1024  # 1MB chunks
        total_read = 0
        
        try:
            with open(output_file, 'wb') as f:
                while total_read < partition.size:
                    # Calculate chunk size for this iteration
                    current_chunk = min(chunk_size, partition.size - total_read)
                    
                    # Read chunk from device
                    data = self._read_partition_chunk(
                        partition.offset + total_read,
                        current_chunk
                    )
                    
                    # Write to file
                    f.write(data)
                    total_read += len(data)
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(total_read, partition.size)
            
            # Verify extraction
            if os.path.getsize(output_file) != partition.size:
                self.logger.warning(f"Size mismatch for {partition.name}")
            
            partition.file_path = str(output_file)
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to extract partition {partition.name}: {e}")
            if output_file.exists():
                output_file.unlink()
            raise
    
    def _read_partition_chunk(self, offset: int, size: int) -> bytes:
        """
        Read a chunk of data from device storage
        This would use MTK protocol to read from EMMC/UFS
        """
        # TODO: Implement actual reading via MTK download mode
        # For now, return dummy data
        return b'\x00' * size
    
    def extract_all_partitions(self, output_dir: Path,
                              progress_callback: Optional[Callable[[str, int, int], None]] = None,
                              status_callback: Optional[Callable[[str, str, str], None]] = None) -> Dict[str, str]:
        """
        Extract all partitions from device
        
        Args:
            output_dir: Directory to save all partitions
            progress_callback: Optional callback (partition_name, current, total)
        
        Returns:
            Dictionary mapping partition names to file paths
        """
        if not self.partitions:
            self.read_partition_table()
        
        extracted = {}
        self.last_failed_partitions = {}
        
        required_partitions = [p for p in self.partitions if self._is_required_for_build(p)]
        skipped_partitions = [p.name for p in self.partitions if not self._is_required_for_build(p)]

        self.logger.info(
            f"Build extraction profile: {len(required_partitions)} required, {len(skipped_partitions)} skipped"
        )
        if skipped_partitions:
            self.logger.info(f"Skipped partitions: {', '.join(skipped_partitions)}")

        for partition in required_partitions:
            self.logger.info(f"Extracting {partition.name}...")

            if status_callback:
                status_callback(partition.name, 'extracting', '')
            
            def part_progress(current, total):
                if progress_callback:
                    progress_callback(partition.name, current, total)
            
            try:
                path = self.extract_partition(partition, output_dir, part_progress)
                extracted[partition.name] = path
                if status_callback:
                    status_callback(partition.name, 'success', '')
            except Exception as e:
                self.logger.error(f"Failed to extract {partition.name}: {e}")
                self.last_failed_partitions[partition.name] = str(e)
                if status_callback:
                    status_callback(partition.name, 'failed', str(e))
                continue
        
        return extracted
    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of partition file"""
        md5 = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                md5.update(chunk)
        
        return md5.hexdigest()
