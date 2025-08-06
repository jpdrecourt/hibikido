"""
TinyDB Database Manager for Hibikidō (Portable Version)
======================================================

Replacement for MongoDB using TinyDB for complete portability.
Maintains same interface as HibikidoDatabase but uses JSON files.
- recordings.json: Source audio files (indexed by path)
- segments.json: Timestamped slices of recordings (reference by source_path)
- effects.json: Audio processing tools (indexed by path)  
- presets.json: Effect configurations (reference by effect_path)
- performances.json: Session logs
- segmentations.json: Batch processing metadata
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
import logging

logger = logging.getLogger(__name__)

class HibikidoDatabase:
    def __init__(self, data_dir: str = "../hibikido-data/database"):
        self.data_dir = os.path.abspath(data_dir)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Database files
        self.recordings_db = None
        self.segments_db = None
        self.effects_db = None
        self.presets_db = None
        self.performances_db = None
        self.segmentations_db = None
    
    def connect(self) -> bool:
        """Initialize TinyDB connections and setup databases."""
        try:
            # Initialize databases with caching for performance
            self.recordings_db = TinyDB(
                os.path.join(self.data_dir, 'recordings.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            self.segments_db = TinyDB(
                os.path.join(self.data_dir, 'segments.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            self.effects_db = TinyDB(
                os.path.join(self.data_dir, 'effects.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            self.presets_db = TinyDB(
                os.path.join(self.data_dir, 'presets.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            self.performances_db = TinyDB(
                os.path.join(self.data_dir, 'performances.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            self.segmentations_db = TinyDB(
                os.path.join(self.data_dir, 'segmentations.json'),
                storage=CachingMiddleware(JSONStorage)
            )
            
            logger.info(f"TinyDB databases connected in: {self.data_dir}")
            return True
            
        except Exception as e:
            logger.error(f"TinyDB connection failed: {e}")
            return False
    
    # RECORDINGS METHODS (path-based)
    
    def add_recording(self, path: str, metadata: Dict[str, Any]) -> bool:
        """Add a new recording with arbitrary metadata using path as unique identifier."""
        try:
            # Check if already exists
            Q = Query()
            if self.recordings_db.search(Q.path == path):
                logger.warning(f"Duplicate recording path: {path}")
                return False
            
            recording = {
                "path": path,
                "created_at": datetime.now().isoformat()
            }
            
            # Add required metadata (description and duration)
            recording.update(metadata)
            
            self.recordings_db.insert(recording)
            logger.info(f"Added recording: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add recording: {e}")
            return False
        
    def get_recording_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get recording by path."""
        try:
            Q = Query()
            results = self.recordings_db.search(Q.path == path)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get recording {path}: {e}")
            return None
    
    def get_all_recordings(self) -> List[Dict[str, Any]]:
        """Get all recordings."""
        try:
            return self.recordings_db.all()
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
            return []
    
    # SEGMENTS METHODS (reference by source_path)
    
    def add_segment(self, source_path: str, segmentation_id: str,
                   start: float, end: float, description: str,
                   embedding_text: str, faiss_index: int,
                   bark_bands_raw: List[float],
                   bark_norm: float,
                   onset_times_low_mid: List[float],
                   onset_times_mid: List[float],
                   onset_times_high_mid: List[float],
                   features: Dict[str, Any]) -> bool:
        """Add a new segment referencing recording by path."""
        try:
            segment = {
                "source_path": source_path,
                "segmentation_id": segmentation_id,
                "start": start,
                "end": end,
                "description": description,
                "embedding_text": embedding_text,
                "created_at": datetime.now().isoformat()
            }

            # All analysis data is required (duration removed - calculated by interface)
            segment["bark_bands_raw"] = bark_bands_raw
            segment["bark_norm"] = bark_norm
            segment["onset_times_low_mid"] = onset_times_low_mid
            segment["onset_times_mid"] = onset_times_mid
            segment["onset_times_high_mid"] = onset_times_high_mid
            segment["features"] = features
            segment["FAISS_index"] = faiss_index
            
            doc_id = self.segments_db.insert(segment)
            logger.info(f"Added segment: {doc_id} - {description[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add segment: {e}")
            return False
    
    def get_segment_by_faiss_id(self, faiss_index: int) -> Optional[Dict[str, Any]]:
        """Get segment by FAISS index."""
        try:
            Q = Query()
            results = self.segments_db.search(Q.FAISS_index == faiss_index)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get segment with FAISS index {faiss_index}: {e}")
            return None
    
    def get_segments_by_recording_path(self, source_path: str) -> List[Dict[str, Any]]:
        """Get all segments for a recording by path."""
        try:
            Q = Query()
            results = self.segments_db.search(Q.source_path == source_path)
            # Sort by start time
            return sorted(results, key=lambda x: x.get('start', 0))
        except Exception as e:
            logger.error(f"Failed to get segments for recording {source_path}: {e}")
            return []
        
    def add_segmentation(self, segmentation_id: str, method: str, 
                    parameters: Dict[str, Any] = None, 
                    description: str = "") -> bool:
        """Add a new segmentation method/run."""
        try:
            # Check if already exists
            Q = Query()
            if self.segmentations_db.search(Q.segmentation_id == segmentation_id):
                logger.warning(f"Duplicate segmentation ID: {segmentation_id}")
                return False
            
            segmentation = {
                "segmentation_id": segmentation_id,
                "method": method,
                "parameters": parameters or {},
                "description": description,
                "created_at": datetime.now().isoformat()
            }
            
            self.segmentations_db.insert(segmentation)
            logger.info(f"Added segmentation: {segmentation_id} - {method}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add segmentation: {e}")
            return False

    def get_segmentation(self, segmentation_id: str) -> Optional[Dict[str, Any]]:
        """Get segmentation by ID."""
        try:
            Q = Query()
            results = self.segmentations_db.search(Q.segmentation_id == segmentation_id)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get segmentation {segmentation_id}: {e}")
            return None
        
    # EFFECTS METHODS (path-based)
    
    def add_effect(self, path: str, name: str, description: str = "") -> bool:
        """Add a new effect using path as unique identifier."""
        try:
            # Check if already exists
            Q = Query()
            if self.effects_db.search(Q.path == path):
                logger.warning(f"Duplicate effect path: {path}")
                return False
            
            effect = {
                "path": path,
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat()
            }
            
            self.effects_db.insert(effect)
            logger.info(f"Added effect: {path} - {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add effect: {e}")
            return False
    
    def get_effect_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get effect by path."""
        try:
            Q = Query()
            results = self.effects_db.search(Q.path == path)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get effect {path}: {e}")
            return None
    
    # PRESETS METHODS (separate collection, reference by effect_path)
    
    def add_preset(self, effect_path: str, parameters: List[Any], 
                  description: str, embedding_text: str, 
                  faiss_index: int = None) -> bool:
        """Add a new preset to separate presets collection."""
        try:
            preset = {
                "effect_path": effect_path,
                "parameters": parameters,
                "description": description,
                "embedding_text": embedding_text,
                "created_at": datetime.now().isoformat()
            }
            
            if faiss_index is not None:
                preset["FAISS_index"] = faiss_index
            
            doc_id = self.presets_db.insert(preset)
            logger.info(f"Added preset: {doc_id} - {description[:50]}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add preset: {e}")
            return False
    
    def get_preset_by_faiss_id(self, faiss_index: int) -> Optional[Dict[str, Any]]:
        """Get preset by FAISS index."""
        try:
            Q = Query()
            results = self.presets_db.search(Q.FAISS_index == faiss_index)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Failed to get preset with FAISS index {faiss_index}: {e}")
            return None
    
    def get_presets_by_effect_path(self, effect_path: str) -> List[Dict[str, Any]]:
        """Get all presets for an effect by path."""
        try:
            Q = Query()
            return self.presets_db.search(Q.effect_path == effect_path)
        except Exception as e:
            logger.error(f"Failed to get presets for effect {effect_path}: {e}")
            return []
    
    def get_segments_without_embeddings(self) -> List[Dict[str, Any]]:
        """Get all segments that don't have FAISS embeddings yet."""
        try:
            Q = Query()
            return self.segments_db.search(~Q.FAISS_index.exists())
        except Exception as e:
            logger.error(f"Failed to get segments without embeddings: {e}")
            return []
    
    def get_presets_without_embeddings(self) -> List[Dict[str, Any]]:
        """Get all presets that don't have FAISS embeddings yet."""
        try:
            Q = Query()
            return self.presets_db.search(~Q.FAISS_index.exists())
        except Exception as e:
            logger.error(f"Failed to get presets without embeddings: {e}")
            return []
    
    # PERFORMANCES METHODS
    
    def add_performance(self, performance_id: str, date: datetime = None) -> bool:
        """Add a new performance session."""
        try:
            # Check if already exists
            Q = Query()
            if self.performances_db.search(Q.performance_id == performance_id):
                logger.warning(f"Duplicate performance ID: {performance_id}")
                return False
            
            performance = {
                "performance_id": performance_id,
                "date": (date or datetime.now()).isoformat(),
                "invocations": [],
                "created_at": datetime.now().isoformat()
            }
            
            self.performances_db.insert(performance)
            logger.info(f"Added performance: {performance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add performance: {e}")
            return False
    
    def add_invocation(self, performance_id: str, text: str, time: float,
                      segment_id: str = None, effect: str = None) -> bool:
        """Add an invocation to a performance."""
        try:
            invocation = {
                "text": text,
                "time": time
            }
            
            if segment_id:
                invocation["segment_id"] = segment_id
            if effect:
                invocation["effect"] = effect
            
            # Update the performance document
            def update_invocations(doc):
                doc['invocations'].append(invocation)
                return doc
            
            Q = Query()
            updated = self.performances_db.update(
                update_invocations,
                Q.performance_id == performance_id
            )
            return len(updated) > 0
            
        except Exception as e:
            logger.error(f"Failed to add invocation to performance {performance_id}: {e}")
            return False
    
    # STATISTICS AND UTILITIES
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            recordings_count = len(self.recordings_db)
            segments_count = len(self.segments_db)
            Q = Query()
            segments_with_embeddings = len(self.segments_db.search(Q.FAISS_index.exists()))
            effects_count = len(self.effects_db)
            presets_count = len(self.presets_db)
            presets_with_embeddings = len(self.presets_db.search(Q.FAISS_index.exists()))
            performances_count = len(self.performances_db)
            segmentations_count = len(self.segmentations_db)
            
            return {
                "recordings": recordings_count,
                "segments": segments_count,
                "segments_with_embeddings": segments_with_embeddings,
                "effects": effects_count,
                "presets": presets_count,
                "presets_with_embeddings": presets_with_embeddings,
                "performances": performances_count,
                "segmentations": segmentations_count,
                "total_searchable_items": segments_with_embeddings + presets_with_embeddings
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    def flush_all(self) -> bool:
        """
        Force TinyDB to flush cached data to JSON files using CachingMiddleware.flush().
        
        Returns:
            True if successful, False otherwise
        """
        try:
            databases = [
                ("recordings", self.recordings_db),
                ("segments", self.segments_db), 
                ("effects", self.effects_db),
                ("presets", self.presets_db),
                ("performances", self.performances_db),
                ("segmentations", self.segmentations_db)
            ]
            
            flushed_count = 0
            for name, db in databases:
                if db is not None:
                    try:
                        # Use CachingMiddleware's flush() method
                        db.storage.flush()
                        flushed_count += 1
                        logger.debug(f"Flushed {name} database using CachingMiddleware.flush()")
                        
                    except Exception as e:
                        logger.warning(f"Failed to flush {name} database: {e}")
            
            if flushed_count > 0:
                # Verify by getting stats
                stats = self.get_stats()
                total_records = sum([
                    stats.get('recordings', 0),
                    stats.get('segments', 0), 
                    stats.get('effects', 0),
                    stats.get('presets', 0),
                    stats.get('performances', 0),
                    stats.get('segmentations', 0)
                ])
                
                logger.info(f"Successfully flushed {flushed_count} databases to JSON files: {total_records} total records")
                return True
            else:
                logger.error("No databases were flushed")
                return False
            
        except Exception as e:
            logger.error(f"Failed to flush databases: {e}")
            return False
    
    def update_recording_description(self, doc_id: int, description: str) -> bool:
        """Update recording description by document ID."""
        try:
            Q = Query()
            updated_count = self.recordings_db.update({'description': description}, doc_id=doc_id)
            if updated_count:
                logger.info(f"Updated recording {doc_id} description")
                return True
            else:
                logger.warning(f"Recording {doc_id} not found for description update")
                return False
        except Exception as e:
            logger.error(f"Failed to update recording {doc_id} description: {e}")
            return False
    
    def update_segment_description(self, doc_id: int, description: str) -> bool:
        """Update segment description by document ID."""
        try:
            Q = Query()
            updated_count = self.segments_db.update({'description': description}, doc_id=doc_id)
            if updated_count:
                logger.info(f"Updated segment {doc_id} description")
                return True
            else:
                logger.warning(f"Segment {doc_id} not found for description update")
                return False
        except Exception as e:
            logger.error(f"Failed to update segment {doc_id} description: {e}")
            return False
    
    # Method removed - recordings no longer store features
    
    def update_segment_features(self, doc_id: int, features: Dict[str, Any]) -> bool:
        """Update segment features by document ID."""
        try:
            Q = Query()
            updated_count = self.segments_db.update({'features': features}, doc_id=doc_id)
            if updated_count:
                logger.info(f"Updated segment {doc_id} features")
                return True
            else:
                logger.warning(f"Segment {doc_id} not found for features update")
                return False
        except Exception as e:
            logger.error(f"Failed to update segment {doc_id} features: {e}")
            return False

    def close(self):
        """Close the database connections."""
        try:
            if self.recordings_db:
                self.recordings_db.close()
            if self.segments_db:
                self.segments_db.close()
            if self.effects_db:
                self.effects_db.close()
            if self.presets_db:
                self.presets_db.close()
            if self.performances_db:
                self.performances_db.close()
            if self.segmentations_db:
                self.segmentations_db.close()
            logger.info("TinyDB connections closed")
        except Exception as e:
            logger.warning(f"Error closing TinyDB connections: {e}")


if __name__ == "__main__":
    # Quick test
    import tempfile
    import shutil
    
    # Create temporary directory for test
    test_dir = tempfile.mkdtemp()
    print(f"Testing TinyDB manager in: {test_dir}")
    
    try:
        db = HibikidoDatabase(test_dir)
        print("✓ TinyDB manager created")
        
        success = db.connect()
        print(f"✓ Connection: {success}")
        
        stats = db.get_stats()
        print(f"✓ Initial stats: {stats}")
        
        # Test adding a recording
        result = db.add_recording('/test/path', {'description': 'Test recording'})
        print(f"✓ Add recording result: {result}")
        
        # Test adding a segment
        result = db.add_segment('/test/path', 'test_seg', 0.0, 1.0, 'Test segment', 'test description')
        print(f"✓ Add segment result: {result}")
        
        final_stats = db.get_stats()
        print(f"✓ Final stats: {final_stats}")
        
        db.close()
        print("✓ Database closed")
        
    finally:
        # Cleanup
        shutil.rmtree(test_dir)
        print(f"✓ Cleaned up test directory")