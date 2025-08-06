"""
Hibikidō Smoke Tests
===================

Basic "does it work?" tests for the core system functionality.
For an artistic project, we prioritize simple validation over exhaustive testing.
"""

import tempfile
import os
from hibikido.component_factory import ComponentFactory
from hibikido.server_config import get_default_config


def test_server_components_initialize():
    """Test that all server components can be created and initialized."""
    # Use temporary directory for test data
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test config with temp paths
        config = get_default_config()
        config['database']['data_dir'] = os.path.join(temp_dir, 'database')
        config['embedding']['index_file'] = os.path.join(temp_dir, 'test.index')
        
        # Create and initialize components
        factory = ComponentFactory(config)
        db_manager, embedding_manager, text_processor, osc_handler, orchestrator = factory.create_components()
        
        # Test initialization
        assert factory.initialize_components(db_manager, embedding_manager, osc_handler), "Component initialization failed"
        
        # Test basic functionality
        stats = db_manager.get_stats()
        assert isinstance(stats, dict), "Database stats should return dict"
        assert stats['recordings'] == 0, "Fresh database should have 0 recordings"
        
        # Test embedding manager
        assert embedding_manager.get_total_embeddings() == 0, "Fresh index should have 0 embeddings"
        
        # Cleanup
        db_manager.close()
        osc_handler.close()
        
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_basic_workflow():
    """Test adding a recording and creating embeddings."""
    temp_dir = tempfile.mkdtemp()
    
    try:
        config = get_default_config()
        config['database']['data_dir'] = os.path.join(temp_dir, 'database')
        config['embedding']['index_file'] = os.path.join(temp_dir, 'test.index')
        
        factory = ComponentFactory(config)
        db_manager, embedding_manager, text_processor, _, _ = factory.create_components()
        
        # Initialize (skip OSC for testing)
        assert db_manager.connect(), "Database connection failed"
        assert embedding_manager.initialize(), "Embedding manager initialization failed"
        
        # Test adding a recording
        success = db_manager.add_recording("/test/audio.wav", {"description": "Test sound"})
        assert success, "Adding recording failed"
        
        # Test adding a segment with all required parameters (no duration stored)
        success = db_manager.add_segment(
            source_path="/test/audio.wav",
            segmentation_id="test",
            start=0.0,
            end=1.0,
            description="Test segment",
            embedding_text="test sound description",
            faiss_index=0,
            bark_bands_raw=[0.1] * 24,
            bark_norm=1.0,
            onset_times_low_mid=[0.5],
            onset_times_mid=[0.3],
            onset_times_high_mid=[0.8],
            features={"test": "value"}
        )
        assert success, "Adding segment failed"
        
        # Test stats after adding content
        stats = db_manager.get_stats()
        assert stats['recordings'] == 1, "Should have 1 recording"
        assert stats['segments'] == 1, "Should have 1 segment"
        
        db_manager.close()
        
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Running Hibikidō smoke tests...")
    test_server_components_initialize()
    print("✓ Component initialization test passed")
    
    test_basic_workflow()
    print("✓ Basic workflow test passed")
    
    print("All smoke tests passed! 🎵")