"""
Configuration module for RELAY
Handles settings, API keys, and configuration management
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

class Config:
    """Configuration manager for RELAY"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # Default config file location
        if config_file is None:
            config_dir = Path.home() / ".relay"
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / "config.json"
        
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "openai_api_key": "",
            "model": "gpt-4-vision-preview",
            "max_iterations": 50,
            "max_failures": 10,
            "confidence_threshold": 3,
            "action_timeout": 30.0,
            "safety": {
                "emergency_stop_enabled": True,
                "confirmation_required": ["delete", "purchase", "confirm", "submit"],
                "destructive_actions": ["delete", "format", "uninstall", "shutdown"],
                "allowed_actions": ["click", "type", "scroll", "wait", "verify", "navigate"]
            },
            "ui": {
                "theme": "dark",
                "window_size": "1200x800",
                "narration_lines": 100
            },
            "logging": {
                "level": "INFO",
                "file": "relay.log",
                "max_size": "10MB"
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self._merge_configs(default_config, loaded_config)
                    self.logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        else:
            self.logger.info("No config file found, using defaults")
        
        return default_config
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]):
        """Recursively merge loaded config with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        self.logger.info(f"Configuration updated: {key} = {value}")
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key from config or environment"""
        # Try config first
        api_key = self.get("openai_api_key")
        if api_key:
            return api_key
        
        # Try environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return api_key
        
        return None
    
    def set_openai_api_key(self, api_key: str):
        """Set OpenAI API key"""
        self.set("openai_api_key", api_key)
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required settings
        if not self.get_openai_api_key():
            errors.append("OpenAI API key not found")
        
        # Check numeric values
        if self.get("max_iterations", 0) <= 0:
            errors.append("max_iterations must be positive")
        
        if self.get("max_failures", 0) <= 0:
            errors.append("max_failures must be positive")
        
        if self.get("confidence_threshold", 0) < 0 or self.get("confidence_threshold", 0) > 10:
            errors.append("confidence_threshold must be between 0 and 10")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            return False
        
        return True
    
    def get_safety_settings(self) -> Dict[str, Any]:
        """Get safety configuration"""
        return self.get("safety", {})
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get("ui", {})
    
    def get_logging_settings(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get("logging", {})
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self._load_config()
        self.save_config()
        self.logger.info("Configuration reset to defaults") 