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
        'database': {
            'data_dir': '../hibikido-data/database'
        },
        'embedding': {
            'model_name': 'all-MiniLM-L6-v2',
            'index_file': '../hibikido-data/index/hibikido.index'
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
            'bark_similarity_threshold': 0.5   # 50%
        },
        'audio': {
            'audio_directory': '../hibikido-data/audio'
        }
    }


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
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
