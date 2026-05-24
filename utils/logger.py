"""
Logging System
"""

import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os

class Logger:
    def __init__(self, name: str = 'Cod3x'):
        self.name = name
        self.logger = None
    
    def setup(self, config: Dict = None, debug: bool = False):
        """Setup logging configuration"""
        config = config or {}
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        
        # Set level
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            level = config.get('level', 'INFO')
            self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        log_format = config.get('format', 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter(log_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = config.get('file', 'cod3x.log')
        if log_file:
            try:
                # Ensure directory exists
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Could not create log file: {e}")
        
        return self.logger
    
    def get_logger(self) -> logging.Logger:
        """Get the logger instance"""
        if not self.logger:
            self.setup()
        return self.logger
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        if self.logger:
            self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        if self.logger:
            self.logger.info(message, *args, **kwargs)
        else:
            print(f"ℹ️ {message}")
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        if self.logger:
            self.logger.warning(message, *args, **kwargs)
        else:
            print(f"⚠️ {message}")
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        if self.logger:
            self.logger.error(message, *args, **kwargs)
        else:
            print(f"❌ {message}")
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        if self.logger:
            self.logger.critical(message, *args, **kwargs)
        else:
            print(f"🚨 {message}")
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        if self.logger:
            self.logger.exception(message, *args, **kwargs)

def setup_logger(config: Dict = None, debug: bool = False) -> Logger:
    """Setup and return a logger instance"""
    logger = Logger('Cod3x')
    logger.setup(config, debug)
    return logger
