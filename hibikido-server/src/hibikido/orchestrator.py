"""
Orchestrator for Hibikidō (Enhanced for Manifestation Protocol)
===============================================================

Manages time-perceptual niches using Bark band cosine similarity.
All results go through the queue - orchestrator decides when to manifest.
"""

import time
import math
import json
from typing import Dict, List, Any, Optional, Callable
import logging
from .bark_analyzer import BarkAnalyzer

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, bark_similarity_threshold: float = 0.5):
        """
        Initialize orchestrator.
        
        Args:
            bark_similarity_threshold: Maximum allowed Bark band cosine similarity (0.5 = 50%)
        """
        self.bark_similarity_threshold = bark_similarity_threshold
        
        # Active niches: list of dicts with manifestation_id, bark_bands_raw, bark_norm
        self.active_niches = []
        
        # Cached ecosystem state for performance
        self.ecosystem_raw = [0.0] * 24
        self.ecosystem_norm = [0.0] * 24
        
        # Queue for manifestations: list of (manifestation_data, request_time)
        self.queue = []
        
        # Callbacks for sending manifestations and niche updates
        self.manifest_callback = None
        self.niche_callback = None
        
        logger.info(f"Orchestrator initialized: {bark_similarity_threshold:.1f} Bark similarity threshold")
    
    def set_manifest_callback(self, callback: Callable):
        """Set callback function for sending manifestations."""
        self.manifest_callback = callback
    
    def set_niche_callback(self, callback: Callable):
        """Set callback function for sending niche updates."""
        self.niche_callback = callback
    
    def queue_manifestation(self, manifestation_data: Dict[str, Any]) -> bool:
        """
        Queue a manifestation for orchestrator processing.
        All search results go through here - no immediate manifestations.
        
        Args:
            manifestation_data: {
                "index": int, "collection": str, "score": float,
                "path": str, "description": str, "start": float, "end": float,
                "parameters": str, "sound_id": str, "bark_bands": List[float], 
                "duration": float
            }
            
        Returns:
            True if queued successfully
        """
        try:
            request_time = time.time()
            self.queue.append((manifestation_data, request_time))
            
            sound_id = manifestation_data.get("sound_id", "unknown")
            logger.debug(f"Queued manifestation: {sound_id}")
            
            # Process queue immediately - event-driven approach
            self._process_queue()
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue manifestation: {e}")
            return False
    
    
    def _process_queue(self):
        """Process the manifestation queue - send manifestations when niches are free."""
        if not self.queue or not self.manifest_callback:
            return
        
        now = time.time()
        remaining_queue = []
        manifestations_sent = 0
        
        # Process queue in FIFO order
        for manifestation_data, request_time in self.queue:
            try:
                # Extract Bark bands info
                sound_id = manifestation_data.get("sound_id", "unknown")
                bark_bands_raw = manifestation_data.get("bark_bands_raw", [0.0] * 24)
                bark_norm = manifestation_data.get("bark_norm", 0.0)
                
                # Check for conflicts against cached ecosystem
                has_conflict = self._find_conflict(bark_bands_raw)
                
                if not has_conflict:
                    # No conflict - generate unique manifestation ID and register niche
                    manifestation_id = f"{manifestation_data['index']}_{int(now * 1000)}"
                    self._register_niche(manifestation_id, bark_bands_raw, bark_norm)
                    
                    # Send manifestation via callback
                    self.manifest_callback(
                        manifestation_id,
                        manifestation_data["collection"],
                        manifestation_data["score"],
                        manifestation_data["path"],
                        manifestation_data["description"],
                        manifestation_data["start"],
                        manifestation_data["end"],
                        manifestation_data["parameters"]
                    )
                    
                    # Send niche update
                    if self.niche_callback:
                        self.niche_callback(manifestation_id, bark_bands_raw)
                    
                    manifestations_sent += 1
                    logger.debug(f"Manifested: {manifestation_id} [Bark norm: {bark_norm:.3f}] "
                               f"(queued for {now - request_time:.1f}s)")
                else:
                    # Still has conflict - keep in queue
                    remaining_queue.append((manifestation_data, request_time))
                    
            except Exception as e:
                logger.error(f"Failed to process queued manifestation: {e}")
                # Drop this manifestation to avoid infinite loops
        
        # Update queue with remaining items
        self.queue = remaining_queue
        
        if manifestations_sent > 0:
            logger.debug(f"Processed queue: {manifestations_sent} manifestations sent, "
                        f"{len(self.queue)} still queued")
    
    def _find_conflict(self, new_sound_raw: List[float]) -> bool:
        """
        Find if new sound conflicts with current ecosystem.
        
        Args:
            new_sound_raw: Raw Bark band energy vector of new sound
            
        Returns:
            True if conflict exists, False otherwise
        """
        if not self.active_niches:
            return False
        
        # Normalize new sound for comparison
        new_sound_norm = BarkAnalyzer.normalize_vector(new_sound_raw)
        
        # Compare against cached normalized ecosystem
        similarity = BarkAnalyzer.cosine_similarity(new_sound_norm, self.ecosystem_norm)
        
        return similarity > self.bark_similarity_threshold
    
    
    def _register_niche(self, manifestation_id: str, bark_bands_raw: List[float], bark_norm: float):
        """Register a new active niche and update cached ecosystem."""
        niche = {
            "manifestation_id": manifestation_id,
            "bark_bands_raw": bark_bands_raw,
            "bark_norm": bark_norm
        }
        self.active_niches.append(niche)
        
        # Update cached ecosystem
        self._update_ecosystem_cache()
    
    def free_manifestation(self, manifestation_id: str) -> bool:
        """Manually free a manifestation by ID and update ecosystem."""
        before_count = len(self.active_niches)
        self.active_niches = [n for n in self.active_niches if n["manifestation_id"] != manifestation_id]
        
        freed = len(self.active_niches) < before_count
        if freed:
            # Update cached ecosystem after removal
            self._update_ecosystem_cache()
            
            # Process queue immediately - new sounds may now fit
            self._process_queue()
            
            logger.debug(f"Freed manifestation: {manifestation_id}")
        else:
            logger.warning(f"Manifestation not found for freeing: {manifestation_id}")
        return freed
    
    def _update_ecosystem_cache(self):
        """Update cached ecosystem raw and normalized vectors."""
        if not self.active_niches:
            self.ecosystem_raw = [0.0] * 24
            self.ecosystem_norm = [0.0] * 24
            return
        
        # Sum all raw vectors
        self.ecosystem_raw = [0.0] * 24
        for niche in self.active_niches:
            for i in range(24):
                self.ecosystem_raw[i] += niche["bark_bands_raw"][i]
        
        # Normalize the combined ecosystem
        self.ecosystem_norm = BarkAnalyzer.normalize_vector(self.ecosystem_raw)
        
        logger.debug(f"Updated ecosystem cache: {len(self.active_niches)} niches, "
                    f"total energy: {BarkAnalyzer.vector_norm(self.ecosystem_raw):.3f}")
    
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "active_niches": len(self.active_niches),
            "queued_requests": len(self.queue),
            "bark_similarity_threshold": self.bark_similarity_threshold
        }
    
