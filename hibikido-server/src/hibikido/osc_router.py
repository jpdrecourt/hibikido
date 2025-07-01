#!/usr/bin/env python3
"""
Hibikidō Server - OSC Router
============================

OSC message routing and handler registration.
"""

import logging
from typing import Dict, Callable, Any

logger = logging.getLogger(__name__)


class OSCRouter:
    """Routes OSC messages to appropriate handlers."""
    
    def __init__(self, osc_handler):
        self.osc_handler = osc_handler
        self.handlers: Dict[str, Callable] = {}
    
    def register_handlers(self, command_handlers):
        """Register all command handlers with OSC."""
        handlers = {
            'invoke': command_handlers.handle_invoke,
            'add_recording': command_handlers.handle_add_recording,
            'add_effect': command_handlers.handle_add_effect,
            'add_segment': command_handlers.handle_add_segment,
            'add_preset': command_handlers.handle_add_preset,
            'rebuild_index': command_handlers.handle_rebuild_index,
            'stats': command_handlers.handle_stats,
            'stop': command_handlers.handle_stop
        }
        
        self.osc_handler.register_handlers(handlers)
        logger.info(f"Registered {len(handlers)} OSC handlers")
    
    def print_banner(self, config: Dict[str, Any], stats: Dict[str, Any], 
                    embedding_count: int, orch_stats: Dict[str, Any]):
        """Print startup banner with information."""
        print("\n" + "="*70)
        print("🎵 HIBIKIDŌ SERVER READY 🎵")
        print("="*70)
        print(f"Database: {stats.get('segments', 0)} segments, "
              f"{stats.get('presets', 0)} presets, "
              f"{stats.get('total_searchable_items', 0)} searchable")
        print(f"FAISS Index: {embedding_count} embeddings")
        print(f"Index file: {config['embedding']['index_file']}")
        print(f"Orchestrator: {orch_stats['bark_similarity_threshold']:.1f} Bark similarity threshold, "
              f"{orch_stats['time_precision']*1000:.0f}ms precision")
        print(f"Listening: {config['osc']['listen_ip']}:{config['osc']['listen_port']}")
        print(f"Sending: {config['osc']['send_ip']}:{config['osc']['send_port']}")
        print("\nOSC Commands:")
        print("  /invoke \"incantation\"           - semantic invocation → manifestations")
        print("  /add_recording \"path\" \"description\" - add recording with Bark band analysis")
        print("  /add_effect \"path\" metadata     - add new effect with default preset")
        print("  /add_segment \"path\" \"description\" metadata - add new segment")
        print("  /add_preset \"text\" metadata     - add new effect preset")
        print("  /rebuild_index                   - rebuild FAISS index from database")
        print("  /stats                           - database and orchestrator statistics")
        print("  /stop                            - shutdown server")
        print("="*70)
        print()
