#!/usr/bin/env python3
"""
Hibikidō Server - Component Factory
===================================

Creates and initializes all server components.
"""

import os
import logging
from typing import Dict, Any, Tuple, Optional

from .tinydb_manager import HibikidoDatabase
from .embedding_manager import EmbeddingManager
from .text_processor import TextProcessor
from .osc_handler import OSCHandler
from .orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class ComponentFactory:
    """Factory for creating and initializing server components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists for index files."""
        index_file = self.config['embedding']['index_file']
        data_dir = os.path.dirname(index_file)
        
        if data_dir and not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                logger.info(f"Created data directory: {data_dir}")
            except Exception as e:
                logger.error(f"Failed to create data directory {data_dir}: {e}")
                # Fall back to current directory
                self.config['embedding']['index_file'] = os.path.basename(index_file)
                logger.warning(f"Falling back to current directory: {self.config['embedding']['index_file']}")
    
    def create_components(self) -> Tuple[HibikidoDatabase, EmbeddingManager, TextProcessor, OSCHandler, Orchestrator]:
        """Create all components."""
        db_manager = HibikidoDatabase(
            data_dir=self.config['database']['data_dir']
        )
        
        embedding_manager = EmbeddingManager(
            model_name=self.config['embedding']['model_name'],
            index_file=self.config['embedding']['index_file']
        )
        
        text_processor = TextProcessor()
        
        osc_handler = OSCHandler(
            listen_ip=self.config['osc']['listen_ip'],
            listen_port=self.config['osc']['listen_port'],
            send_ip=self.config['osc']['send_ip'],
            send_port=self.config['osc']['send_port']
        )
        
        orchestrator = Orchestrator(
            overlap_threshold=self.config['orchestrator']['overlap_threshold'],
            time_precision=self.config['orchestrator']['time_precision']
        )
        
        return db_manager, embedding_manager, text_processor, osc_handler, orchestrator
    
    def initialize_components(self, db_manager: HibikidoDatabase, 
                            embedding_manager: EmbeddingManager,
                            osc_handler: OSCHandler) -> bool:
        """Initialize all components that need initialization."""
        logger.info("Initializing components...")
        
        # Initialize database
        if not db_manager.connect():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize embedding system
        if not embedding_manager.initialize():
            logger.error("Failed to initialize embedding system")
            return False
        
        # Initialize OSC
        if not osc_handler.initialize():
            logger.error("Failed to initialize OSC")
            return False
        
        logger.info("All components initialized successfully")
        return True
