"""
Text Processor for Hibikidō (Simplified)
========================================

Minimal processing for embedding text from hierarchical context.
Designed for prompt-engineered descriptions with all-MiniLM-L6-v2.
Priority: segment > segmentation > recording (local > broader)
"""

import re
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self, max_chars: int = 400):
        """
        Initialize with character limit instead of word limit.
        
        Args:
            max_chars: Maximum characters for combined text (default 400)
        """
        self.max_chars = max_chars
    
    def create_segment_embedding_text(self, segment: Dict[str, Any], 
                                    recording: Dict[str, Any] = None,
                                    segmentation: Dict[str, Any] = None) -> str:
        """
        Create embedding text for a segment using hierarchical context.
        Uses descriptions as-is when available, minimal processing.
        Priority: segment > segmentation > recording
        """
        try:
            # Priority 1: Segment description (local) - use as-is if good
            segment_desc = segment.get("description", "")
            if segment_desc and len(segment_desc.strip()) > 10:
                # Use segment description directly - it's prompt-engineered
                return self._normalize_text(segment_desc)
            
            # Fallback: Combine contexts for sparse descriptions
            contexts = []
            
            if segment_desc:
                contexts.append(segment_desc)
            
            # Priority 2: Segmentation description (method context)
            if segmentation:
                seg_desc = segmentation.get("description", "")
                if seg_desc:
                    contexts.append(seg_desc)
            
            # Priority 3: Recording description (broader context)
            if recording:
                rec_desc = recording.get("description", "")
                if rec_desc:
                    contexts.append(rec_desc)
            
            # Combine contexts with character limit
            combined = self._combine_contexts(contexts)
            
            if not combined:
                combined = "audio segment"
            
            logger.debug(f"Segment embedding text: '{combined}' for {segment.get('_id', 'unknown')}")
            return combined
            
        except Exception as e:
            logger.error(f"Failed to create segment embedding text: {e}")
            return self._normalize_text(segment.get("description", "audio segment"))
    
    def create_preset_embedding_text(self, preset: Dict[str, Any],
                                   effect: Dict[str, Any] = None) -> str:
        """
        Create embedding text for an effect preset.
        Uses descriptions as-is when available.
        Priority: preset > effect
        """
        try:
            # Priority 1: Preset description (local) - use as-is if good
            preset_desc = preset.get("description", "")
            if preset_desc and len(preset_desc.strip()) > 10:
                return self._normalize_text(preset_desc)
            
            # Fallback: Combine contexts
            contexts = []
            
            if preset_desc:
                contexts.append(preset_desc)
            
            # Priority 2: Effect description (broader context)
            if effect:
                effect_desc = effect.get("description", "")
                if effect_desc:
                    contexts.append(effect_desc)
            
            combined = self._combine_contexts(contexts)
            
            if not combined:
                combined = "effect preset"
            
            logger.debug(f"Preset embedding text: '{combined}' for preset in {effect.get('_id', 'unknown') if effect else 'unknown'}")
            return combined
            
        except Exception as e:
            logger.error(f"Failed to create preset embedding text: {e}")
            return self._normalize_text(preset.get("description", "effect preset"))
    
    def _combine_contexts(self, contexts: list) -> str:
        """
        Combine context descriptions with character limit.
        Uses descriptions as-is, just concatenates and truncates if needed.
        """
        if not contexts:
            return ""
        
        # Filter out empty contexts
        valid_contexts = [self._normalize_text(ctx) for ctx in contexts if ctx and ctx.strip()]
        
        if not valid_contexts:
            return ""
        
        # If only one context, use it directly
        if len(valid_contexts) == 1:
            return self._truncate_text(valid_contexts[0])
        
        # Multiple contexts: join with separator
        combined = " | ".join(valid_contexts)
        
        return self._truncate_text(combined)
    
    def _normalize_text(self, text: str) -> str:
        """
        Minimal text normalization - just clean whitespace.
        Preserves the prompt-engineered semantic content.
        """
        if not text:
            return ""
        
        text = str(text).strip()
        
        # Only normalize whitespace - preserve all semantic content
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _truncate_text(self, text: str, suffix: str = "...") -> str:
        """
        Truncate text to character limit if needed.
        Tries to break at word boundaries.
        """
        if len(text) <= self.max_chars:
            return text
        
        # Try to truncate at word boundary
        truncate_point = self.max_chars - len(suffix)
        
        # Find last space before truncate point
        last_space = text.rfind(' ', 0, truncate_point)
        
        if last_space > truncate_point * 0.8:  # If we don't lose too much
            return text[:last_space] + suffix
        else:
            # Just truncate at character limit
            return text[:truncate_point] + suffix
