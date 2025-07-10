#!/usr/bin/env python3
"""
Hibikidō Server - Command Handlers
==================================

OSC command implementations.
"""

import json
import logging
import os
from typing import Dict, Any
from .audio_analyzer import analyze_loaded_audio

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Handles all OSC command implementations."""
    
    def __init__(self, config: Dict[str, Any], db_manager, embedding_manager, 
                 text_processor, osc_handler, orchestrator):
        self.config = config
        self.db_manager = db_manager
        self.embedding_manager = embedding_manager
        self.text_processor = text_processor
        self.osc_handler = osc_handler
        self.orchestrator = orchestrator
    
    def handle_invoke(self, unused_addr: str, *args):
        """Handle invocation requests - queue all results for manifestation."""
        try:
            parsed = self.osc_handler.parse_args(*args)
            incantation = parsed.get('arg1', '').strip()
            
            if not incantation:
                self.osc_handler.send_error("invoke requires incantation text")
                return
            
            logger.info(f"Invocation: '{incantation}'")
            
            # Search with MongoDB lookups
            results = self.embedding_manager.search(
                incantation, 
                self.config['search']['top_k'],
                db_manager=self.db_manager
            )
            
            if not results:
                self.osc_handler.send_confirm("no resonance found")
                return
            
            # Filter to segments only (MVP requirement)
            segment_results = [r for r in results if r["collection"] == "segments"]
            
            # Filter by minimum score
            min_score = self.config['search']['min_score']
            segment_results = [r for r in segment_results if r["score"] >= min_score]
            
            if not segment_results:
                self.osc_handler.send_confirm("no segment resonance found")
                return
            
            # Queue ALL results for orchestrator processing
            queued_count = 0
            for i, result in enumerate(segment_results):
                document = result["document"]
                
                # Extract metadata for orchestrator
                bark_bands_raw = document.get("bark_bands_raw", [0.0] * 24)
                bark_norm = document.get("bark_norm", 0.0)
                sound_id = str(getattr(document, 'doc_id', document.get('source_path', 'unknown')))
                
                # Prepare manifestation data
                manifestation_data = {
                    "index": i,
                    "collection": "segments",
                    "score": float(result["score"]),
                    "path": str(document.get("source_path", "")),
                    "description": self._create_display_description(
                        document.get("embedding_text", "")
                    ),
                    "start": float(document.get("start", 0.0)),
                    "end": float(document.get("end", 1.0)),
                    "parameters": "[]",  # Empty for segments
                    "sound_id": sound_id,
                    "bark_bands_raw": bark_bands_raw,
                    "bark_norm": bark_norm
                }
                
                # Queue for orchestrator (immediate processing per sound)
                if self.orchestrator.queue_manifestation(manifestation_data):
                    queued_count += 1
            
            # Simple confirmation - no completion signal
            self.osc_handler.send_confirm(f"invoked: {queued_count} resonances queued")
            logger.info(f"Invocation '{incantation}' queued {queued_count} manifestations")
            
        except Exception as e:
            error_msg = f"invocation failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def _create_display_description(self, embedding_text: str) -> str:
        """Create human-readable description from embedding text."""
        try:
            if not embedding_text:
                return "untitled"
            
            # Simple processing for performance
            words = embedding_text.split()
            
            # Take first few meaningful words
            meaningful_words = []
            for word in words[:8]:
                word = word.strip().lower()
                if len(word) > 2 and word not in ['the', 'and', 'for', 'with']:
                    meaningful_words.append(word)
                if len(meaningful_words) >= 4:
                    break
            
            if meaningful_words:
                description = " ".join(meaningful_words[:4])
                # Capitalize first word
                if description:
                    description = description[0].upper() + description[1:]
                return description[:50]
            
            return embedding_text[:30].strip() or "untitled"
            
        except Exception as e:
            logger.warning(f"Failed to create display description: {e}")
            return "untitled"
    
    def handle_add_recording(self, unused_addr: str, *args):
        """Handle add recording requests with simplified syntax: /add_recording [file_path] "[description]"."""
        logger.info(f"HANDLER ENTRY: handle_add_recording called with {len(args)} args")
        try:
            if len(args) < 2:
                self.osc_handler.send_error("add_recording requires file path and description")
                return

            relative_path = str(args[0]).strip()
            description = str(args[1]).strip()
            
            if not relative_path:
                self.osc_handler.send_error("add_recording requires file path")
                return
            if not description:
                self.osc_handler.send_error("add_recording requires description")
                return
            
            # Resolve audio path from config
            audio_dir = self.config.get('audio_directory', '../hibikido-data/audio')
            full_audio_path = os.path.join(audio_dir, relative_path)
            
            # Check if file exists
            if not os.path.exists(full_audio_path):
                self.osc_handler.send_error(f"audio file not found: {full_audio_path}")
                return
            
            # Just get basic duration for recording metadata - no analysis yet
            try:
                import librosa
                y, sr = librosa.load(full_audio_path, sr=22050)
                duration = len(y) / sr
                logger.info(f"Recording duration: {duration:.2f}s")
            except Exception as e:
                self.osc_handler.send_error(f"failed to load audio file: {e}")
                return
            
            # Prepare metadata
            metadata = {
                'description': description,
                'duration': duration
            }
            
            # Add recording to database with metadata
            success = self.db_manager.add_recording(
                path=relative_path,  # Store relative path
                metadata=metadata
            )
            
            if not success:
                self.osc_handler.send_error(f"recording already exists or failed to add: {relative_path}")
                return
            
            # Auto-create full-length segment with complete analysis
            segment_description = f"Full recording: {description}"
            
            segment_embedding_text = self.text_processor.create_segment_embedding_text(
                segment={'description': segment_description},
                recording={'description': description, 'path': relative_path, **metadata},
                segmentation={'description': 'Auto-generated full recording segment'}
            )
            
            # Add embedding
            faiss_id = self.embedding_manager.add_embedding(segment_embedding_text)
            
            # Perform complete analysis only for the segment using already loaded audio
            try:
                analysis = analyze_loaded_audio(y, sr)
                logger.info(f"Segment analysis: {analysis['duration']:.2f}s, "
                           f"Bark norm: {analysis['bark_norm']:.3f}, "
                           f"{analysis['onset_count']} onsets ({analysis['onset_density']:.1f}/sec)")
            except Exception as e:
                logger.warning(f"Segment analysis failed, using defaults: {e}")
                analysis = {
                    'duration': duration,
                    'bark_bands_raw': [0.0] * 24,
                    'bark_norm': 0.0,
                    'onset_count': 0,
                    'onset_density': 0.0
                }
            
            # Add auto-segment with complete analysis
            segment_success = self.db_manager.add_segment(
                source_path=relative_path,  # Store relative path
                segmentation_id="auto_full",
                start=0.0,
                end=1.0,
                description=segment_description,
                embedding_text=segment_embedding_text,
                faiss_index=faiss_id,
                bark_bands_raw=analysis['bark_bands_raw'],
                bark_norm=analysis['bark_norm'],
                duration=analysis['duration'],
                onset_count=analysis['onset_count'],
                onset_density=analysis['onset_density']
            )
            
            if segment_success:
                self.osc_handler.send_confirm(f"added recording: {relative_path} with auto-segment")
                logger.info(f"Added recording: {relative_path} with auto-segment at FAISS {faiss_id}")
            else:
                self.osc_handler.send_confirm(f"added recording: {relative_path} (segment creation failed)")
                
        except Exception as e:
            error_msg = f"add_recording failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)

    def handle_add_effect(self, unused_addr: str, *args):
        """Handle add effect requests."""
        try:
            parsed = self.osc_handler.parse_args(*args)
            path = parsed.get('arg1', '').strip()
            metadata_str = parsed.get('arg2', '{}')
            
            if not path:
                self.osc_handler.send_error("add_effect requires effect path")
                return
            
            try:
                metadata = json.loads(metadata_str) if metadata_str != '{}' else {}
            except json.JSONDecodeError:
                self.osc_handler.send_error("invalid metadata JSON")
                return
            
            name = metadata.get('name', path.split('/')[-1].split('.')[0])
            description = metadata.get('description', f"Effect: {name}")
            
            success = self.db_manager.add_effect(
                path=path,
                name=name,
                description=description
            )
            
            if not success:
                self.osc_handler.send_error(f"effect already exists or failed to add: {path}")
                return
            
            # Create default preset
            preset_description = f"Default preset: {description}"
            preset_embedding_text = self.text_processor.create_preset_embedding_text(
                preset={'description': preset_description},
                effect={'description': description, 'name': name, 'path': path}
            )
            
            faiss_id = self.embedding_manager.add_embedding(preset_embedding_text)
            
            preset_success = self.db_manager.add_preset(
                effect_path=path,
                parameters=[],
                description=preset_description,
                embedding_text=preset_embedding_text,
                faiss_index=faiss_id
            )
            
            if preset_success:
                self.osc_handler.send_confirm(f"added effect: {path} with default preset")
                logger.info(f"Added effect: {path} with default preset at FAISS {faiss_id}")
            else:
                self.osc_handler.send_confirm(f"added effect: {path} (preset creation failed)")
                
        except Exception as e:
            error_msg = f"add_effect failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)

    def handle_add_segment(self, unused_addr: str, *args):
        """Handle add segment requests using path, description, and optional metadata pairs."""
        try:
            if len(args) < 2:
                self.osc_handler.send_error(
                    "add_segment requires source_path and description")
                return

            source_path = str(args[0]).strip()
            description = str(args[1]).strip()

            if not source_path:
                self.osc_handler.send_error("add_segment requires source_path")
                return
            if not description:
                self.osc_handler.send_error("add_segment requires description")
                return

            metadata: Dict[str, Any] = {}
            if len(args) > 2:
                if (len(args) - 2) % 2 != 0:
                    self.osc_handler.send_error("metadata must be name/value pairs")
                    return
                for i in range(2, len(args), 2):
                    key = str(args[i])
                    value = str(args[i + 1]) if i + 1 < len(args) else ""
                    metadata[key] = value

            segmentation_id = metadata.get('segmentation_id', 'manual')
            start = float(metadata.get('start', 0.0))
            end = float(metadata.get('end', 1.0))
            duration = float(metadata.get('duration', 0.0))

            if not source_path:
                self.osc_handler.send_error("source_path required")
                return
            if not (0.0 <= start <= 1.0) or not (0.0 <= end <= 1.0) or start >= end:
                self.osc_handler.send_error("invalid start/end values (must be 0.0-1.0)")
                return
            
            recording = self.db_manager.get_recording_by_path(source_path)
            if not recording:
                self.osc_handler.send_error(f"recording not found: {source_path}")
                return
            
            # Get full audio path for analysis
            audio_dir = self.config.get('audio_directory', '../hibikido-data/audio')
            full_audio_path = os.path.join(audio_dir, source_path)
            
            # Load audio once and analyze this segment
            try:
                import librosa
                y, sr = librosa.load(full_audio_path, sr=22050)
                
                # Convert relative times to absolute for analysis
                total_duration = recording.get('duration', len(y) / sr)
                abs_start = start * total_duration
                abs_end = end * total_duration
                
                analysis = analyze_loaded_audio(y, sr, abs_start, abs_end)
                logger.info(f"Segment analysis: {analysis['onset_count']} onsets, "
                           f"{analysis['onset_density']:.1f} onsets/sec, "
                           f"Bark norm: {analysis['bark_norm']:.3f}")
            except Exception as e:
                logger.warning(f"Segment analysis failed, using defaults: {e}")
                analysis = {
                    'bark_bands_raw': [0.0] * 24,
                    'bark_norm': 0.0,
                    'onset_count': 0,
                    'onset_density': 0.0
                }
            
            embedding_text = self.text_processor.create_segment_embedding_text(
                segment={'description': description},
                recording=recording,
                segmentation={'description': f'Manual segmentation: {segmentation_id}'}
            )
            
            faiss_id = self.embedding_manager.add_embedding(embedding_text)
            if faiss_id is None:
                self.osc_handler.send_error("failed to create embedding")
                return

            success = self.db_manager.add_segment(
                source_path=source_path,
                segmentation_id=segmentation_id,
                start=start,
                end=end,
                description=description,
                embedding_text=embedding_text,
                faiss_index=faiss_id,
                duration=duration,
                bark_bands_raw=analysis.get('bark_bands_raw'),
                bark_norm=analysis.get('bark_norm'),
                onset_count=analysis.get('onset_count'),
                onset_density=analysis.get('onset_density')
            )
            
            if success:
                self.osc_handler.send_confirm(f"added segment for {source_path} [{start}-{end}]")
                logger.info(f"Added segment for {source_path} at FAISS {faiss_id}")
            else:
                self.osc_handler.send_error("failed to add segment to database")
                
        except Exception as e:
            error_msg = f"add_segment failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)

    def handle_add_preset(self, unused_addr: str, *args):
        """Handle add preset requests."""
        try:
            parsed = self.osc_handler.parse_args(*args)
            description = parsed.get('arg1', '').strip()
            metadata_str = parsed.get('arg2', '{}')
            
            if not description:
                self.osc_handler.send_error("add_preset requires description")
                return
            
            try:
                metadata = json.loads(metadata_str) if metadata_str != '{}' else {}
            except json.JSONDecodeError:
                self.osc_handler.send_error("invalid metadata JSON")
                return
            
            effect_path = metadata.get('effect_path')
            if not effect_path:
                self.osc_handler.send_error("effect_path required in metadata")
                return
            
            parameters = metadata.get('parameters', [])
            
            effect = self.db_manager.get_effect_by_path(effect_path)
            if not effect:
                self.osc_handler.send_error(f"effect not found: {effect_path}")
                return
            
            embedding_text = self.text_processor.create_preset_embedding_text(
                preset={'description': description, 'parameters': parameters},
                effect=effect
            )
            
            faiss_id = self.embedding_manager.add_embedding(embedding_text)
            if faiss_id is None:
                self.osc_handler.send_error("failed to create embedding")
                return
            
            success = self.db_manager.add_preset(
                effect_path=effect_path,
                parameters=parameters,
                description=description,
                embedding_text=embedding_text,
                faiss_index=faiss_id
            )
            
            if success:
                self.osc_handler.send_confirm(f"added preset for {effect_path}")
                logger.info(f"Added preset for {effect_path} at FAISS {faiss_id}")
            else:
                self.osc_handler.send_error("failed to add preset to database")
                
        except Exception as e:
            error_msg = f"add_preset failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_rebuild_index(self, unused_addr: str, *args):
        """Handle rebuild index requests."""
        try:
            logger.info("Rebuilding FAISS index from database...")
            
            stats = self.embedding_manager.rebuild_from_database(
                self.db_manager, 
                self.text_processor
            )
            
            result_msg = f"index rebuilt: {stats['segments_added']} segments, {stats['presets_added']} presets"
            if stats['errors'] > 0:
                result_msg += f" ({stats['errors']} errors)"
            
            self.osc_handler.send_confirm(result_msg)
            logger.info(f"Index rebuild completed: {result_msg}")
            
        except Exception as e:
            error_msg = f"rebuild_index failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_stats(self, unused_addr: str, *args):
        """Handle stats requests (includes orchestrator)."""
        try:
            stats = self.db_manager.get_stats()
            embedding_count = self.embedding_manager.get_total_embeddings()
            orch_stats = self.orchestrator.get_stats()
            
            # Send detailed stats
            stats_msg = (f"Database: {stats.get('recordings', 0)} recordings, "
                        f"{stats.get('segments', 0)} segments, "
                        f"{stats.get('effects', 0)} effects, "
                        f"{stats.get('presets', 0)} presets. "
                        f"FAISS: {embedding_count} embeddings. "
                        f"Orchestrator: {orch_stats['active_niches']} active, "
                        f"{orch_stats['queued_requests']} queued")
            
            self.osc_handler.send_confirm(stats_msg)
            
            # Also send as structured data
            self.osc_handler.client.send_message("/stats_result", [
                stats.get("recordings", 0),
                stats.get("segments", 0),
                stats.get("effects", 0),
                stats.get("presets", 0),
                embedding_count,
                orch_stats["active_niches"],
                orch_stats["queued_requests"]
            ])
            
            logger.info(f"Stats: {stats_msg}")
            
        except Exception as e:
            error_msg = f"stats failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
            
    def handle_free(self, unused_addr: str, *args):
        """Handle free manifestation requests."""
        try:
            if len(args) < 1:
                self.osc_handler.send_error("free requires manifestation_id")
                return
            
            manifestation_id = str(args[0]).strip()
            
            if not manifestation_id:
                self.osc_handler.send_error("free requires manifestation_id")
                return
            
            # Free the manifestation in orchestrator
            freed = self.orchestrator.free_manifestation(manifestation_id)
            
            if freed:
                self.osc_handler.send_confirm(f"freed: {manifestation_id}")
                logger.info(f"Freed manifestation: {manifestation_id}")
            else:
                self.osc_handler.send_error(f"manifestation not found: {manifestation_id}")
                
        except Exception as e:
            error_msg = f"free failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_save(self, unused_addr: str, *args):
        """Handle explicit save requests for database and FAISS index."""
        try:
            logger.info("Saving database and FAISS index...")
            
            # Save database
            db_saved = self.db_manager.save_all()
            
            # Save FAISS index
            index_saved = self.embedding_manager.force_save_index()
            
            if db_saved and index_saved:
                self.osc_handler.send_confirm("saved database and index")
                logger.info("Database and FAISS index saved successfully")
            elif db_saved:
                self.osc_handler.send_error("database saved, index save failed")
                logger.warning("Database saved but FAISS index save failed")
            elif index_saved:
                self.osc_handler.send_error("index saved, database save failed")
                logger.warning("FAISS index saved but database save failed")
            else:
                self.osc_handler.send_error("save failed")
                logger.error("Both database and FAISS index save failed")
                
        except Exception as e:
            error_msg = f"save failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_stop(self, unused_addr: str, *args):
        """Handle stop requests."""
        logger.info("Received stop command")
        self.osc_handler.send_confirm("stopping")
        # Note: actual shutdown is handled by main server
