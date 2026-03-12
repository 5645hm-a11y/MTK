"""
Scatter File Generator
Creates and updates scatter files for SP Flash Tool
"""

import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from core.partition_extractor import PartitionInfo


class ScatterFileGenerator:
    """Generate scatter files compatible with SP Flash Tool"""
    
    # Scatter file template structure
    HEADER_TEMPLATE = """############################################################################################################
#
#  General Setting
#
############################################################################################################
- general: MTK_PLATFORM_CFG
  info: 
    - config_version: V1.1.2
      platform: {platform}
      project: {project}
      storage: {storage}
      boot_channel: {boot_channel}
      block_size: {block_size}
#
############################################################################################################
#
#  Layout Setting
#
############################################################################################################
"""

    PARTITION_TEMPLATE = """- partition_index: SYS{index}
  partition_name: {name}
  file_name: {filename}
  is_download: {is_download}
  type: {type}
  linear_start_addr: {linear_start}
  physical_start_addr: {physical_start}
  partition_size: {partition_size}
  region: {region}
  storage: {storage}
  boundary_check: {boundary_check}
  is_reserved: {is_reserved}
  operation_type: {operation_type}
  d_type: {d_type}
  reserve: {reserve}

"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def generate(self, partitions: List[PartitionInfo], 
                output_path: Path,
                chip_model: str = "MT6580",
                project_name: str = "project") -> str:
        """
        Generate scatter file from partition list
        
        Args:
            partitions: List of partition information
            output_path: Path where scatter file will be saved
            chip_model: MTK chip model (e.g., MT6580, MT6765)
            project_name: Project name for scatter file
        
        Returns:
            Path to generated scatter file
        """
        self.logger.info(f"Generating scatter file for {chip_model}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate header
        header = self.HEADER_TEMPLATE.format(
            platform=chip_model,
            project=project_name,
            storage="EMMC",
            boot_channel="MSDC_0",
            block_size="0x20000"
        )
        
        # Generate partition entries
        partition_entries = []
        for idx, partition in enumerate(partitions):
            entry = self._generate_partition_entry(partition, idx)
            partition_entries.append(entry)
        
        # Combine all parts
        scatter_content = header + "".join(partition_entries)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(scatter_content)
        
        self.logger.info(f"Scatter file created: {output_path}")
        return str(output_path)
    
    def _generate_partition_entry(self, partition: PartitionInfo, index: int) -> str:
        """Generate scatter file entry for a single partition"""
        
        # Determine partition properties
        is_download = "true" if partition.name not in ["userdata", "cache"] else "false"
        
        # Determine partition type
        if partition.name == "preloader":
            ptype = "NORMAL_ROM"
        elif partition.name in ["boot", "recovery"]:
            ptype = "ANDROID"
        else:
            ptype = "NORMAL_ROM"
        
        # Use existing file path or generate default
        filename = partition.file_path if partition.file_path else f"{partition.name}.img"
        if '\\' in filename or '/' in filename:
            filename = Path(filename).name
        
        return self.PARTITION_TEMPLATE.format(
            index=index,
            name=partition.name,
            filename=filename,
            is_download=is_download,
            type=ptype,
            linear_start=f"0x{partition.linear_start_addr:08x}",
            physical_start=f"0x{partition.offset:08x}",
            partition_size=f"0x{partition.partition_size:08x}",
            region="EMMC_USER",
            storage="HW_STORAGE_EMMC",
            boundary_check="true",
            is_reserved="false",
            operation_type="UPDATE",
            d_type="NUTL_ADDR",
            reserve="0x00"
        )
    
    def parse_scatter_file(self, scatter_path: Path) -> List[PartitionInfo]:
        """
        Parse existing scatter file to extract partition information
        
        Args:
            scatter_path: Path to scatter file
        
        Returns:
            List of partition information
        """
        self.logger.info(f"Parsing scatter file: {scatter_path}")
        
        partitions = []
        
        try:
            with open(scatter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into partition blocks
            blocks = content.split('- partition_index:')
            
            for block in blocks[1:]:  # Skip header
                partition = self._parse_partition_block(block)
                if partition:
                    partitions.append(partition)
            
            self.logger.info(f"Parsed {len(partitions)} partitions from scatter file")
            return partitions
            
        except Exception as e:
            self.logger.error(f"Failed to parse scatter file: {e}")
            raise
    
    def _parse_partition_block(self, block: str) -> Optional[PartitionInfo]:
        """Parse a single partition block from scatter file"""
        try:
            lines = block.strip().split('\n')
            info = {}
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            
            # Extract required fields
            name = info.get('partition_name', '').strip()
            if not name:
                return None
            
            # Parse hex values
            linear_start = int(info.get('linear_start_addr', '0x0').replace('0x', ''), 16)
            physical_start = int(info.get('physical_start_addr', '0x0').replace('0x', ''), 16)
            partition_size = int(info.get('partition_size', '0x0').replace('0x', ''), 16)
            
            return PartitionInfo(
                name=name,
                size=partition_size,
                offset=physical_start,
                type=info.get('type', 'NORMAL_ROM'),
                file_path=info.get('file_name'),
                linear_start_addr=linear_start,
                partition_size=partition_size
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse partition block: {e}")
            return None
    
    def update_scatter_file(self, scatter_path: Path, 
                           updated_partitions: List[PartitionInfo]) -> str:
        """
        Update existing scatter file with modified partition information
        
        Args:
            scatter_path: Path to existing scatter file
            updated_partitions: Updated partition list
        
        Returns:
            Path to updated scatter file
        """
        # Create backup
        backup_path = scatter_path.with_suffix('.scatter.backup')
        if scatter_path.exists():
            import shutil
            shutil.copy(scatter_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
        
        # Read original to preserve metadata
        chip_model = "MT6580"  # TODO: Extract from original
        project_name = "project"  # TODO: Extract from original
        
        # Generate new scatter file
        return self.generate(updated_partitions, scatter_path, chip_model, project_name)
