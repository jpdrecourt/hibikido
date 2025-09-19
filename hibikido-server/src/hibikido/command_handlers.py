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
from .visualizer import AudioVisualizer

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
        self.visualizer = AudioVisualizer(config.get('audio', {}).get('sample_rate', 44100))  # Will use native SR
    
    def handle_invoke(self, unused_addr: str, *args):
        """
        Handle invocation requests - queue all results for manifestation.
        
        OSC: /invoke "incantation text"
        Performs semantic search and queues matching segments for orchestrated manifestation.
        """
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
                segment_id = str(getattr(document, 'doc_id', 'unknown'))
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
                    "parameters": json.dumps({"segment_id": segment_id}),
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
        """
        Handle add recording requests with 3-band onset analysis.
        
        OSC: /add_recording "file_path" "description"
        Adds recording with auto-generated full-length segment including onset times for 3 bands.
        """
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
            
            # Get basic duration for recording metadata - no downsampling, preserve original SR
            try:
                import librosa
                y, sr = librosa.load(full_audio_path, sr=None)  # Preserve original sample rate
                duration = len(y) / sr
                logger.info(f"Recording duration: {duration:.2f}s at {sr}Hz")
            except Exception as e:
                self.osc_handler.send_error(f"failed to load audio file: {e}")
                return
            
            # Prepare metadata (no features yet - will be added in segment analysis)
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
            
            # Perform complete analysis for the segment using already loaded audio
            analysis = analyze_loaded_audio(y, sr)
            total_onsets = len(analysis['onset_times_low_mid']) + len(analysis['onset_times_mid']) + len(analysis['onset_times_high_mid'])
            logger.info(f"Segment analysis: {analysis['duration']:.2f}s at {sr}Hz, "
                       f"Bark norm: {analysis['bark_norm']:.3f}, "
                       f"{total_onsets} total onsets across 3 bands")
                       
            # No longer storing features in recording - only in segments
            
            # Add auto-segment with complete analysis including features (no duration stored)
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
                onset_times_low_mid=analysis['onset_times_low_mid'],
                onset_times_mid=analysis['onset_times_mid'],
                onset_times_high_mid=analysis['onset_times_high_mid'],
                features=analysis['features']
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
        """
        Handle add segment requests with onset times analysis.
        
        OSC: /add_segment "source_path" "description" ["start" 0.1 "end" 0.6]
        Adds timed segment with complete Bark band and 3-band onset analysis.
        """
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
            
            # Load audio and analyze this segment - preserve original sample rate
            import librosa
            y, sr = librosa.load(full_audio_path, sr=None)
            
            # Convert relative times to absolute for analysis
            total_duration = recording['duration']
            abs_start = start * total_duration
            abs_end = end * total_duration
            
            analysis = analyze_loaded_audio(y, sr, abs_start, abs_end)
            total_onsets = len(analysis['onset_times_low_mid']) + len(analysis['onset_times_mid']) + len(analysis['onset_times_high_mid'])
            logger.info(f"Segment analysis: {total_onsets} total onsets across 3 bands, "
                       f"Bark norm: {analysis['bark_norm']:.3f}")
            
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
                bark_bands_raw=analysis['bark_bands_raw'],
                bark_norm=analysis['bark_norm'],
                onset_times_low_mid=analysis['onset_times_low_mid'],
                onset_times_mid=analysis['onset_times_mid'],
                onset_times_high_mid=analysis['onset_times_high_mid'],
                features=analysis['features']
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
    
    def handle_flush(self, unused_addr: str, *args):
        """Handle explicit database flush to ensure JSON files are up to date."""
        try:
            logger.info("Flushing database to JSON files...")
            
            # Force flush all cached data to JSON files
            flushed = self.db_manager.flush_all()
            
            if flushed:
                stats = self.db_manager.get_stats()
                total_records = (stats.get('recordings', 0) + 
                               stats.get('segments', 0) + 
                               stats.get('effects', 0) + 
                               stats.get('presets', 0))
                
                self.osc_handler.send_confirm(f"flushed to disk: {total_records} records")
                logger.info(f"Successfully flushed {total_records} records to JSON files")
            else:
                self.osc_handler.send_error("flush failed")
                logger.error("Database flush failed")
                
        except Exception as e:
            error_msg = f"flush failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_visualize(self, unused_addr: str, *args):
        """
        Handle segment visualization requests.
        
        OSC: /visualize <segment_id>
        Shows multi-band onset analysis visualization for the specified segment ID (integer).
        """
        try:
            if len(args) < 1:
                self.osc_handler.send_error("visualize requires segment ID (integer)")
                return
                
            # Directly get integer argument
            try:
                segment_id = int(args[0])
            except (ValueError, TypeError):
                self.osc_handler.send_error(f"segment ID must be an integer, got: {args[0]}")
                return
                
            logger.info(f"Visualizing segment: {segment_id}")
            
            # Get all segments and find the requested one by doc_id
            segments = self.db_manager.get_all_segments()
            segment = None
            
            for s in segments:
                if s.doc_id == segment_id:
                    segment = s
                    break
                    
            if not segment:
                self.osc_handler.send_error(f"segment {segment_id} not found")
                return
                
            source_path = segment.get('source_path')
            start_ratio = segment.get('start', 0.0)
            end_ratio = segment.get('end', 1.0)
            
            if not source_path:
                self.osc_handler.send_error(f"no source_path for segment {segment_id}")
                return
                
            # Resolve full audio path
            audio_dir = self.config.get('audio_directory', '../hibikido-data/audio')
            full_audio_path = os.path.join(audio_dir, source_path)
            
            # Check if file exists
            if not os.path.exists(full_audio_path):
                self.osc_handler.send_error(f"audio file not found: {full_audio_path}")
                return
                
            # Get recording to convert relative times to absolute
            recording = self.db_manager.get_recording_by_path(source_path)
            if not recording:
                self.osc_handler.send_error(f"recording not found for segment {segment_id}")
                return
                
            total_duration = recording.get('duration', 0.0)
            start_time = start_ratio * total_duration
            end_time = end_ratio * total_duration
                
            # Create visualization
            self.visualizer.visualize_segment_multiband(full_audio_path, start_time, end_time)
            
            self.osc_handler.send_confirm(f"visualized segment {segment_id}")
            logger.info(f"Successfully visualized segment {segment_id}")
            
        except Exception as e:
            error_msg = f"visualization failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_list_segments(self, unused_addr: str, *args):
        """
        Handle list segments requests - shows segment IDs and descriptions.
        
        OSC: /list_segments
        Lists first 10 segments with their doc_id, description, and source info.
        """
        try:
            segments = self.db_manager.get_all_segments()
            
            if not segments:
                self.osc_handler.send_confirm("no segments found")
                return
                
            logger.info(f"Found {len(segments)} segments:")
            for segment in segments[:10]:  # Limit to first 10 to avoid spam
                desc = segment.get('description', 'No description')[:50]
                source = segment.get('source_path', 'Unknown')
                start = segment.get('start', 0.0)
                end = segment.get('end', 0.0)
                logger.info(f"  ID {segment.doc_id}: '{desc}' ({source} {start:.1f}s-{end:.1f}s)")
                
            if len(segments) > 10:
                logger.info(f"  ... and {len(segments) - 10} more segments")
                
            self.osc_handler.send_confirm(f"listed {min(10, len(segments))} of {len(segments)} segments")
            
        except Exception as e:
            error_msg = f"list segments failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)
    
    def handle_get_segment_field(self, unused_addr: str, *args):
        """
        Handle get segment field requests - returns specific field value for a segment.

        OSC: /get_segment_field [segment_id] [field_name]
        Returns: /segment_field [segment_id] [field_name] [value]
        """
        try:
            parsed = self.osc_handler.parse_args(*args)
            segment_id_str = parsed.get('arg1', '').strip()
            field_name = parsed.get('arg2', '').strip()

            if not segment_id_str or not field_name:
                self.osc_handler.send_error("get_segment_field requires segment_id and field_name")
                return

            try:
                segment_id = int(segment_id_str)
            except ValueError:
                self.osc_handler.send_error(f"invalid segment_id: {segment_id_str}")
                return

            # Get all segments and find the requested one by doc_id
            segments = self.db_manager.get_all_segments()
            target_segment = None
            for s in segments:
                if s.doc_id == segment_id:
                    target_segment = s
                    break

            if target_segment is None:
                self.osc_handler.send_error(f"segment not found: {segment_id}")
                return

            # Get the requested field
            if hasattr(target_segment, field_name):
                field_value = getattr(target_segment, field_name)
            elif field_name in target_segment:
                field_value = target_segment[field_name]
            elif field_name.startswith('features.') and 'features' in target_segment:
                # Handle nested features access like "features.spectral_entropy_mean"
                feature_key = field_name.split('.', 1)[1]
                features = target_segment.get('features', {})
                if feature_key in features:
                    field_value = features[feature_key]
                else:
                    self.osc_handler.send_error(f"feature not found: {feature_key}")
                    return
            else:
                self.osc_handler.send_error(f"field not found: {field_name}")
                return

            # Send the result
            self.osc_handler.client.send_message(self.osc_handler.addresses['segment_field'], [
                str(segment_id), field_name, str(field_value)
            ])
            logger.debug(f"Sent segment field: {segment_id}.{field_name} = {field_value}")

        except Exception as e:
            error_msg = f"get_segment_field failed: {e}"
            logger.error(error_msg)
            self.osc_handler.send_error(error_msg)

    def handle_stop(self, unused_addr: str, *args):
        """Handle stop requests."""
        logger.info("Received stop command")
        self.osc_handler.send_confirm("stopping")
        # Note: actual shutdown is handled by main server
