"""
Test to verify Faster-Whisper is the default ASR backend.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFasterWhisperDefault:
    """Test that Faster-Whisper is the default ASR backend"""
    
    def test_faster_whisper_is_default(self):
        """Test that Faster-Whisper is used by default when no env var is set"""
        with patch.dict(os.environ, {}, clear=True):
            # Set required env vars
            os.environ['API_KEY'] = 'test-key'
            os.environ['LOCAL_STORAGE_PATH'] = '/tmp'
            
            # Import config after setting env vars
            from config import ENABLE_OPENAI_WHISPER
            
            # Verify ENABLE_OPENAI_WHISPER is False by default
            assert ENABLE_OPENAI_WHISPER == False, "ENABLE_OPENAI_WHISPER should be False by default"
    
    def test_openai_whisper_requires_explicit_enable(self):
        """Test that OpenAI Whisper requires explicit enabling"""
        with patch.dict(os.environ, {'ENABLE_OPENAI_WHISPER': 'true'}, clear=True):
            # Set required env vars
            os.environ['API_KEY'] = 'test-key'
            os.environ['LOCAL_STORAGE_PATH'] = '/tmp'
            
            # Reimport config to pick up new env var
            import importlib
            import config
            importlib.reload(config)
            
            # Verify ENABLE_OPENAI_WHISPER is True when explicitly set
            assert config.ENABLE_OPENAI_WHISPER == True, "ENABLE_OPENAI_WHISPER should be True when explicitly set"
    
    @patch('services.asr.model_loader.FASTER_WHISPER_AVAILABLE', True)
    @patch('services.asr.model_loader.WhisperModel')
    def test_model_loader_uses_faster_whisper_by_default(self, mock_whisper_model):
        """Test that model loader uses Faster-Whisper by default"""
        with patch.dict(os.environ, {}, clear=True):
            # Set required env vars
            os.environ['API_KEY'] = 'test-key'
            os.environ['LOCAL_STORAGE_PATH'] = '/tmp'
            
            # Mock the WhisperModel
            mock_model_instance = MagicMock()
            mock_whisper_model.return_value = mock_model_instance
            
            # Import and test model loader
            from services.asr.model_loader import load_model
            
            # Load model (should use Faster-Whisper)
            model = load_model(force_reload=True)
            
            # Verify WhisperModel was called (Faster-Whisper)
            assert mock_whisper_model.called, "WhisperModel should be instantiated"
            assert model is not None, "Model should be loaded"
    
    @patch('services.asr.model_loader.FASTER_WHISPER_AVAILABLE', True)
    def test_model_loader_skips_when_openai_whisper_enabled(self):
        """Test that model loader skips Faster-Whisper when OpenAI Whisper is enabled"""
        with patch.dict(os.environ, {'ENABLE_OPENAI_WHISPER': 'true'}, clear=True):
            # Set required env vars
            os.environ['API_KEY'] = 'test-key'
            os.environ['LOCAL_STORAGE_PATH'] = '/tmp'
            
            # Reimport to pick up env changes
            import importlib
            import services.asr.model_loader as model_loader
            importlib.reload(model_loader)
            
            # Load model (should return None when OpenAI Whisper is enabled)
            model = model_loader.load_model(force_reload=True)
            
            # Verify model is None
            assert model is None, "Model should be None when ENABLE_OPENAI_WHISPER=true"
    
    def test_transcription_service_logs_correct_backend(self):
        """Test that transcription service logs the correct backend being used"""
        from unittest.mock import patch, MagicMock
        import logging
        
        # Test 1: Default (Faster-Whisper)
        with patch.dict(os.environ, {}, clear=True):
            os.environ['API_KEY'] = 'test-key'
            os.environ['LOCAL_STORAGE_PATH'] = '/tmp'
            
            with patch('services.v1.media.media_transcribe.logger') as mock_logger:
                with patch('services.v1.media.media_transcribe.download_file') as mock_download:
                    with patch('services.asr.get_model') as mock_get_model:
                        mock_download.return_value = '/tmp/test.wav'
                        mock_model = MagicMock()
                        mock_get_model.return_value = mock_model
                        
                        with patch('os.remove'):
                            try:
                                from services.v1.media.media_transcribe import process_transcribe_media
                                process_transcribe_media(
                                    'http://test.com/audio.wav',
                                    'transcribe',
                                    True, False, False, False,
                                    'direct', 'en', 'test-job'
                                )
                            except:
                                pass  # We're only checking logs
                        
                        # Check that correct log message was used
                        log_calls = [str(call) for call in mock_logger.info.call_args_list]
                        assert any('Faster-Whisper' in str(call) for call in log_calls), \
                            "Should log Faster-Whisper usage"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
