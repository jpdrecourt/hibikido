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
    def __init__(self, bark_similarity_threshold: float = 0.5, time_precision: float = 0.1):
        """
        Initialize orchestrator.
        
        Args:
            bark_similarity_threshold: Maximum allowed Bark band cosine similarity (0.5 = 50%)
            time_precision: Time precision in seconds (0.1 = 100ms)
        """
        self.bark_similarity_threshold = bark_similarity_threshold
        self.time_precision = time_precision
        
        # Active niches: list of dicts with manifestation_id, start_time, end_time, bark_bands
        self.active_niches = []
        
        # Queue for manifestations: list of (manifestation_data, request_time)
        self.queue = []
        
        # Callback for sending manifestations
        self.manifest_callback = None
        
        logger.info(f"Orchestrator initialized: {bark_similarity_threshold:.1f} Bark similarity threshold, "
                   f"{time_precision*1000:.0f}ms precision")
    
    def set_manifest_callback(self, callback: Callable):
        """Set callback function for sending manifestations."""
        self.manifest_callback = callback
    
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
            bark_bands = manifestation_data.get("bark_bands", [0.0] * 24)
            
            logger.debug(f"Queued manifestation: {sound_id} [Bark bands sum: {sum(bark_bands):.3f}]")
            return True
            
        except Exception as e:
            logger.error(f"Failed to queue manifestation: {e}")
            return False
    
    def update(self):
        """
        Periodic update: clean expired niches and process queue.
        This is where manifestations actually get sent.
        """
        try:
            # Clean up expired niches
            self._cleanup_expired()
            
            # Process queue - try to manifest waiting sounds
            self._process_queue()
            
        except Exception as e:
            logger.error(f"Orchestrator update failed: {e}")
    
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
                # Extract Bark bands/duration info
                sound_id = manifestation_data.get("sound_id", "unknown")
                bark_bands = manifestation_data.get("bark_bands", [0.0] * 24)
                duration = float(manifestation_data.get("duration", 1.0))
                
                # Check for conflicts
                conflict_end_time = self._find_conflict(bark_bands, now)
                
                if conflict_end_time is None:
                    # No conflict - generate unique manifestation ID and register niche
                    manifestation_id = f"{manifestation_data['index']}_{int(now * 1000)}"
                    self._register_niche(manifestation_id, now, now + duration, bark_bands)
                    
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
                    
                    manifestations_sent += 1
                    logger.debug(f"Manifested: {manifestation_id} [Bark sum: {sum(bark_bands):.3f}] "
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
    
    def _find_conflict(self, bark_bands: List[float], now: float) -> Optional[float]:
        """
        Find if Bark bands conflict with active niches.
        
        Returns:
            None if no conflict, otherwise the end_time of the earliest conflicting niche
        """
        earliest_conflict_end = None
        
        for niche in self.active_niches:
            # Check time overlap (sound is still active)
            if now < niche["end_time"]:
                # Check Bark band similarity
                similarity = BarkAnalyzer.cosine_similarity(bark_bands, niche["bark_bands"])
                if similarity > self.bark_similarity_threshold:
                    if earliest_conflict_end is None or niche["end_time"] < earliest_conflict_end:
                        earliest_conflict_end = niche["end_time"]
        
        return earliest_conflict_end
    
    
    def _register_niche(self, manifestation_id: str, start_time: float, end_time: float,
                       bark_bands: List[float]):
        """Register a new active niche."""
        niche = {
            "manifestation_id": manifestation_id,
            "start_time": start_time,
            "end_time": end_time,
            "bark_bands": bark_bands
        }
        self.active_niches.append(niche)
    
    def free_manifestation(self, manifestation_id: str) -> bool:
        """Manually free a manifestation by ID."""
        before_count = len(self.active_niches)
        self.active_niches = [n for n in self.active_niches if n["manifestation_id"] != manifestation_id]
        
        freed = len(self.active_niches) < before_count
        if freed:
            logger.debug(f"Freed manifestation: {manifestation_id}")
        else:
            logger.warning(f"Manifestation not found for freeing: {manifestation_id}")
        return freed
    
    def _cleanup_expired(self):
        """Remove expired niches (legacy - now niches are freed manually)."""
        # Keep this method for backward compatibility but it's no longer used
        # since niches are freed manually via /free command
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "active_niches": len(self.active_niches),
            "queued_requests": len(self.queue),
            "bark_similarity_threshold": self.bark_similarity_threshold,
            "time_precision": self.time_precision
        }
    
    # Legacy method for backward compatibility (no longer used)
    def evaluate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method - now everything goes through queue."""
        logger.warning("evaluate_request() called - should use queue_manifestation() instead")
        return {"status": "allowed", "start_time": time.time()}