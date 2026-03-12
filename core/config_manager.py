"""
Configuration Manager
Loads and manages application configuration
"""

import yaml
import logging
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.config = {}
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self.logger.warning(f"Config file not found: {self.config_file}")
                self._load_defaults()
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration"""
        self.config = {
            'application': {
                'name': 'MTK Firmware Editor Pro',
                'version': '1.0.0'
            },
            'device': {
                'connection_timeout': 30
            },
            'mtk': {
                'vendor_id': '0x0e8d',
                'product_ids': ['0x0003', '0x2000', '0x201c']
            },
            'partitions': {
                'common': [
                    'preloader', 'lk', 'boot', 'recovery',
                    'system', 'vendor', 'userdata', 'cache'
                ]
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        Example: config.get('application.name')
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by key (supports dot notation)
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
