#!/usr/bin/env python3
"""
Hibikidō Server - Main Application (Invocation Protocol)
========================================================

Music server using invocation paradigm - sounds manifest when the cosmos permits.
All search results queue through orchestrator, no completion signals.
"""

import signal
import sys
import argparse
import logging
import threading
import time
from typing import Dict, Any

from .server_config import get_default_config, load_config, merge_config
from .component_factory import ComponentFactory
from .command_handlers import CommandHandlers
from .osc_router import OSCRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HibikidoServer:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = merge_config(get_default_config(), config or {})
        
        # Create components
        self.factory = ComponentFactory(self.config)
        (self.db_manager, self.embedding_manager, self.text_processor, 
         self.osc_handler, self.orchestrator) = self.factory.create_components()
        
        # Create command handlers and router
        self.command_handlers = CommandHandlers(
            self.config, self.db_manager, self.embedding_manager,
            self.text_processor, self.osc_handler, self.orchestrator
        )
        self.osc_router = OSCRouter(self.osc_handler)
        
        self.is_running = False
        self.update_thread = None
    
    def initialize(self) -> bool:
        """Initialize all components."""
        logger.info("Initializing Hibikidō Server...")
        
        # Initialize core components
        if not self.factory.initialize_components(
            self.db_manager, self.embedding_manager, self.osc_handler
        ):
            return False
        
        # Setup orchestrator callback
        self.orchestrator.set_manifest_callback(self.osc_handler.send_manifest)
        
        # Register OSC handlers
        self.osc_router.register_handlers(self.command_handlers)
        
        logger.info("All components initialized successfully")
        return True
    
    def start(self):
        """Start the server."""
        try:
            logger.info("Starting Hibikidō Server...")
            
            # Setup graceful shutdown
            signal.signal(signal.SIGINT, self._shutdown_handler)
            signal.signal(signal.SIGTERM, self._shutdown_handler)
            
            # Start OSC server
            server = self.osc_handler.start_server()
            if not server:
                logger.error("Failed to start OSC server")
                return
            self.is_running = True

            # Start orchestrator update thread
            self._start_orchestrator_updates()
            
            # Send ready signal
            self.osc_handler.send_ready()
            
            # Print startup banner
            self._print_banner()
            
            # Start serving
            logger.info("Ready - waiting for invocations...")
            server.serve_forever()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.shutdown()
    
    def _start_orchestrator_updates(self):
        """Start background thread for orchestrator updates."""
        def update_loop():
            while self.is_running:
                try:
                    self.orchestrator.update()
                    time.sleep(self.config['orchestrator']['time_precision'])
                except Exception as e:
                    logger.error(f"Orchestrator update error: {e}")
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        logger.info("Orchestrator update thread started")
    
    def _print_banner(self):
        """Print startup banner with information."""
        stats = self.db_manager.get_stats()
        embedding_count = self.embedding_manager.get_total_embeddings()
        orch_stats = self.orchestrator.get_stats()
        
        self.osc_router.print_banner(self.config, stats, embedding_count, orch_stats)
    
    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Shutdown the server gracefully."""
        if not self.is_running:
            return
        
        logger.info("Shutting down Hibikidō Server...")
        self.is_running = False
        
        try:
            self.osc_handler.close()
            self.db_manager.close()
            logger.info("Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        sys.exit(0)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Hibikidō Server')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Create and start server
    server = HibikidoServer(config)
    
    if not server.initialize():
        logger.error("Failed to initialize server")
        sys.exit(1)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        server.shutdown()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        server.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()