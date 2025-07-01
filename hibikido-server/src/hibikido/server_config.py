#!/usr/bin/env python3
"""
Hibikidō Server - Configuration Management
==========================================

Configuration loading and default settings.
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_default_config() -> Dict[str, Any]:
    """Default configuration settings."""
    return {
        'mongodb': {
            'uri': 'mongodb://localhost:27017',
            'database': 'hibikido'
        },
        'embedding': {
            'model_name': 'all-MiniLM-L6-v2',
            'index_file': 'data/hibikido.index'
        },
        'osc': {
            'listen_ip': '127.0.0.1',
            'listen_port': 9000,
            'send_ip': '127.0.0.1',
            'send_port': 9001
        },
        'search': {
            'top_k': 10,
            'min_score': 0.3
        },
        'orchestrator': {
            'overlap_threshold': 0.2,  # 20%
            'time_precision': 0.1      # 100ms
        }
    }


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {e}")
        return {}


def merge_config(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge override config into base config."""
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    
    return result
