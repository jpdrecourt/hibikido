"""
Hibikidō - Semantic Search Engine for Musical Sounds and Effects
================================================================

A semantic search engine that maps natural language descriptions to audio content
using neural embeddings and hierarchical database design, with real-time orchestration
for time-frequency niche management.

Interaction through OSC protocol only - use HibikidoServer as the single entry point.
"""

__version__ = "0.1.2"
__author__ = "Jean-Philippe Drecourt"

# Public API - single entry point
from .main_server import HibikidoServer

__all__ = [
    "HibikidoServer",
]