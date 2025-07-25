"""
OSC Handler for Hibikidō Server (Updated for Invocation Protocol)
================================================================

Handles all OSC communication using the new invocation paradigm.
/invoke → /manifest (no completion signals)
"""

import json
from typing import List, Dict, Any
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient
import logging

logger = logging.getLogger(__name__)

class OSCHandler:
    def __init__(self, listen_ip: str = "127.0.0.1", listen_port: int = 9000,
                 send_ip: str = "127.0.0.1", send_port: int = 9001):
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.send_ip = send_ip
        self.send_port = send_port
        
        self.client = None
        self.server = None
        self.dispatcher = None
        
        # OSC Address definitions (updated for invocation protocol)
        self.addresses = {
            # Input addresses
            'invoke': '/invoke',  # Changed from 'search'
            'add_recording': '/add_recording',
            'add_effect': '/add_effect', 
            'add_segment': '/add_segment',
            'add_preset': '/add_preset',
            'rebuild_index': '/rebuild_index',
            'stats': '/stats',
            'free': '/free',
            'stop': '/stop',
            
            # Output addresses
            'manifest': '/manifest',  # Changed from 'result'
            'niche': '/niche',       # Niche status for ecosystem visualization
            'confirm': '/confirm',
            'stats_result': '/stats_result',
            'error': '/error'
            # Removed 'search_complete'
        }
    
    def initialize(self) -> bool:
        """Initialize OSC client and server."""
        try:
            # Setup client for sending messages
            self.client = SimpleUDPClient(self.send_ip, self.send_port)
            
            # Setup dispatcher for routing incoming messages
            self.dispatcher = Dispatcher()
            
            logger.info(f"Hibikidō OSC: Initialized - listening: {self.listen_ip}:{self.listen_port}, "
                       f"sending: {self.send_ip}:{self.send_port}")
            return True
            
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to initialize: {e}")
            return False
    
    def register_handlers(self, handlers: Dict[str, callable]):
        """Register message handlers with the dispatcher."""
        logger.info(f"Hibikidō OSC: Registering {len(handlers)} handlers")
        for address_name, handler_func in handlers.items():
            if address_name in self.addresses:
                osc_address = self.addresses[address_name]
                logger.info(f"Hibikidō OSC: Mapping {osc_address} -> {handler_func.__name__}")
                self.dispatcher.map(osc_address, handler_func)
                logger.debug(f"Hibikidō OSC: Registered handler for {osc_address}")
            else:
                logger.warning(f"Hibikidō OSC: Unknown OSC address: {address_name}")
    
    def start_server(self) -> BlockingOSCUDPServer:
        """Start the OSC server."""
        try:
            self.server = BlockingOSCUDPServer(
                (self.listen_ip, self.listen_port), 
                self.dispatcher
            )
            logger.info(f"Hibikidō OSC: Server started on {self.listen_ip}:{self.listen_port}")
            return self.server
            
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to start server: {e}")
            return None
    
    def send_manifest(self, manifestation_id: str, collection: str, score: float, 
                     path: str, description: str, start: float, end: float, 
                     parameters: str = "[]"):
        """Send manifestation message (replaces send_result)."""
        try:
            self.client.send_message(self.addresses['manifest'], [
                manifestation_id, collection, score, path, description, start, end, parameters
            ])
            logger.debug(f"Hibikidō OSC: Sent manifestation: {manifestation_id} - {description}")
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to send manifestation: {e}")
    
    def send_niche(self, manifestation_id: str, bark_bands_raw: List[float]):
        """Send niche status message for ecosystem visualization."""
        try:
            # Send manifestation_id followed by 24 bark band values
            message_data = [manifestation_id] + bark_bands_raw
            self.client.send_message(self.addresses['niche'], message_data)
            logger.debug(f"Hibikidō OSC: Sent niche: {manifestation_id}")
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to send niche: {e}")
    
    def send_confirm(self, message: str):
        """Send confirmation message."""
        try:
            self.client.send_message(self.addresses['confirm'], message)
            logger.debug(f"Hibikidō OSC: Sent confirmation: {message}")
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to send confirmation: {e}")
    
    def send_error(self, error_message: str):
        """Send error message (lightweight for performance)."""
        try:
            self.client.send_message(self.addresses['error'], error_message)
            logger.warning(f"Hibikidō OSC: Sent error: {error_message}")
        except Exception as e:
            logger.error(f"Hibikidō OSC: Failed to send error message: {e}")
    
    def send_ready(self):
        """Send ready signal."""
        self.send_confirm("hibikido_server_ready")
    
    @staticmethod
    def parse_args(*args) -> Dict[str, Any]:
        """Return all OSC arguments as strings indexed by arg1, arg2, ..."""
        parsed: Dict[str, Any] = {}

        for i, arg in enumerate(args):
            parsed[f"arg{i + 1}"] = str(arg) if arg is not None else ""

        return parsed
    
    def close(self):
        """Close OSC connections."""
        try:
            if self.server:
                self.server.server_close()
                logger.info("Hibikidō OSC: Server closed")
        except Exception as e:
            logger.error(f"Hibikidō OSC: Error closing server: {e}")