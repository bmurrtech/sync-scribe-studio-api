"""
Unit and Integration tests for ASR transcription functionality.
Tests both faster-whisper and OpenAI Whisper paths.
Following TDD: RED -> GREEN -> REFACTOR approach
"""

import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, ANY
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.v1.media.media_transcribe import (
    process_transcribe_media,
    _map_faster_whisper_segment,
    _transcribe_with_faster_whisper
)


class TestASRModelSelection:
    """Test model selection based on ENABLE_FASTER_WHISPER flag"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_uses_faster_whisper_when_enabled(self, mock_download, mock_get_model):
        """Test that faster-whisper is used when ENABLE_FASTER_WHISPER is True"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Create mock segments
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Test transcription"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert mock_get_model.called
        assert mock_model.transcribe.called
        assert result[0] == "Test transcription"  # Text result
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', False)
    @patch('services.v1.media.media_transcribe.download_file')
    def test_uses_openai_whisper_when_disabled(self, mock_download):
        """Test that OpenAI Whisper is used when ENABLE_FASTER_WHISPER is False"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        
        mock_model.transcribe.return_value = {
            'text': "Test transcription",
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.0,
                    'text': "Test transcription"
                }
            ],
            'language': 'en'
        }
        
        # Mock whisper module dynamically imported in the function
        import sys
        mock_whisper = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        sys.modules['whisper'] = mock_whisper
        
        try:
            # Act
            with patch('os.remove'):
                result = process_transcribe_media(
                    "http://test.com/audio.wav",
                    "transcribe",
                    include_text=True,
                    include_srt=False,
                    include_segments=False,
                    word_timestamps=False,
                    response_type="direct",
                    language="en",
                    job_id="test-123",
                    words_per_line=None
                )
            
            # Assert
            assert mock_whisper.load_model.called
            assert mock_model.transcribe.called
            assert result[0] == "Test transcription"  # Text result
        finally:
            # Clean up the mock
            if 'whisper' in sys.modules:
                del sys.modules['whisper']
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.whisper')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_fallback_to_openai_when_faster_whisper_unavailable(self, mock_download, mock_whisper, mock_get_model):
        """Test fallback to OpenAI Whisper when faster-whisper model is not available"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_get_model.return_value = None  # Faster-whisper not available
        
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        
        mock_model.transcribe.return_value = {
            'text': "Fallback transcription",
            'segments': [
                {
                    'start': 0.0,
                    'end': 2.0,
                    'text': "Fallback transcription"
                }
            ],
            'language': 'en'
        }
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert mock_get_model.called
        assert mock_whisper.load_model.called  # Fallback to OpenAI
        assert result[0] == "Fallback transcription"


class TestTranscriptionOutput:
    """Test transcription output format consistency between models"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    def test_faster_whisper_segment_mapping(self):
        """Test mapping of faster-whisper segment to OpenAI format"""
        # Arrange
        mock_segment = MagicMock()
        mock_segment.start = 0.5
        mock_segment.end = 2.5
        mock_segment.text = " Hello world "
        
        # Mock word objects
        mock_word1 = MagicMock()
        mock_word1.start = 0.5
        mock_word1.end = 1.0
        mock_word1.word = "Hello"
        mock_word1.probability = 0.95
        
        mock_word2 = MagicMock()
        mock_word2.start = 1.0
        mock_word2.end = 2.5
        mock_word2.word = "world"
        mock_word2.probability = 0.98
        
        mock_segment.words = [mock_word1, mock_word2]
        
        # Act
        result = _map_faster_whisper_segment(mock_segment)
        
        # Assert
        assert result['start'] == 0.5
        assert result['end'] == 2.5
        assert result['text'] == " Hello world "
        assert len(result['words']) == 2
        assert result['words'][0]['word'] == "Hello"
        assert result['words'][0]['probability'] == 0.95
        assert result['words'][1]['word'] == "world"
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_identical_json_output_format(self, mock_download, mock_get_model):
        """Test that both models produce identical JSON structure for text output"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Create mock segments
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Identical output test"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result_text, result_srt, result_segments = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=True,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert isinstance(result_text, str)
        assert result_text == "Identical output test"
        assert isinstance(result_segments, list)
        assert len(result_segments) == 1
        assert 'start' in result_segments[0]
        assert 'end' in result_segments[0]
        assert 'text' in result_segments[0]


class TestWordTimestamps:
    """Test word-level timestamp functionality"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_word_timestamps_enabled(self, mock_download, mock_get_model):
        """Test that word timestamps are properly extracted when enabled"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Create mock segment with words
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 3.0
        mock_segment.text = "Words with timestamps"
        
        mock_word1 = MagicMock()
        mock_word1.start = 0.0
        mock_word1.end = 1.0
        mock_word1.word = "Words"
        mock_word1.probability = 0.95
        
        mock_word2 = MagicMock()
        mock_word2.start = 1.0
        mock_word2.end = 2.0
        mock_word2.word = "with"
        mock_word2.probability = 0.98
        
        mock_word3 = MagicMock()
        mock_word3.start = 2.0
        mock_word3.end = 3.0
        mock_word3.word = "timestamps"
        mock_word3.probability = 0.99
        
        mock_segment.words = [mock_word1, mock_word2, mock_word3]
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result_text, result_srt, result_segments = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=True,
                word_timestamps=True,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert mock_model.transcribe.called
        call_args = mock_model.transcribe.call_args
        assert call_args[1]['word_timestamps'] == True
        assert len(result_segments) == 1
        assert 'words' in result_segments[0]
        assert len(result_segments[0]['words']) == 3
        assert result_segments[0]['words'][0]['word'] == "Words"
        assert result_segments[0]['words'][2]['word'] == "timestamps"


class TestSRTGeneration:
    """Test SRT subtitle generation functionality"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_srt_generation_basic(self, mock_download, mock_get_model):
        """Test basic SRT generation from transcription segments"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Create mock segments
        mock_segment1 = MagicMock()
        mock_segment1.start = 0.0
        mock_segment1.end = 2.0
        mock_segment1.text = "First subtitle"
        mock_segment1.words = []
        
        mock_segment2 = MagicMock()
        mock_segment2.start = 2.0
        mock_segment2.end = 4.0
        mock_segment2.text = "Second subtitle"
        mock_segment2.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment1, mock_segment2], mock_info)
        
        # Act
        with patch('os.remove'):
            result_text, result_srt, result_segments = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=False,
                include_srt=True,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert result_srt is not None
        assert "1\n00:00:00,000 --> 00:00:02,000\nFirst subtitle" in result_srt
        assert "2\n00:00:02,000 --> 00:00:04,000\nSecond subtitle" in result_srt
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_srt_generation_with_words_per_line(self, mock_download, mock_get_model):
        """Test SRT generation with words_per_line parameter"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        # Create mock segment with multiple words
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 6.0
        mock_segment.text = "This is a longer sentence with many words"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result_text, result_srt, result_segments = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=False,
                include_srt=True,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=3  # Split into groups of 3 words
            )
        
        # Assert
        assert result_srt is not None
        # Should have multiple subtitle entries, each with max 3 words
        assert "This is a" in result_srt
        assert "longer sentence with" in result_srt
        assert "many words" in result_srt


class TestResponseTypes:
    """Test different response types (direct vs cloud)"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_direct_response_type(self, mock_download, mock_get_model):
        """Test direct response type returns actual content"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Direct response test"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=True,
                include_segments=True,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert isinstance(result[0], str)  # Text content
        assert isinstance(result[1], str)  # SRT content
        assert isinstance(result[2], list)  # Segments
        assert result[0] == "Direct response test"
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    @patch('builtins.open', new_callable=MagicMock)
    def test_cloud_response_type(self, mock_open, mock_download, mock_get_model):
        """Test cloud response type saves files and returns paths"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Cloud response test"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "en"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=True,
                include_segments=True,
                word_timestamps=False,
                response_type="cloud",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert isinstance(result[0], str)  # File path for text
        assert isinstance(result[1], str)  # File path for SRT
        assert isinstance(result[2], str)  # File path for segments
        assert "test-123.txt" in result[0]
        assert "test-123.srt" in result[1]
        assert "test-123.json" in result[2]


class TestLanguageHandling:
    """Test language detection and specification"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_language_specification(self, mock_download, mock_get_model):
        """Test that specified language is passed to the model"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Bonjour le monde"
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "fr"
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="fr",  # Specify French
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert mock_model.transcribe.called
        call_args = mock_model.transcribe.call_args
        assert call_args[1]['language'] == 'fr'
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_translation_task(self, mock_download, mock_get_model):
        """Test translation task (translate to English)"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_segment = MagicMock()
        mock_segment.start = 0.0
        mock_segment.end = 2.0
        mock_segment.text = "Hello world"  # Translated text
        mock_segment.words = []
        
        mock_info = MagicMock()
        mock_info.language = "fr"  # Original language
        
        mock_model.transcribe.return_value = ([mock_segment], mock_info)
        
        # Act
        with patch('os.remove'):
            result = process_transcribe_media(
                "http://test.com/audio.wav",
                "translate",  # Translation task
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language=None,
                job_id="test-123",
                words_per_line=None
            )
        
        # Assert
        assert mock_model.transcribe.called
        call_args = mock_model.transcribe.call_args
        assert call_args[1]['task'] == 'translate'


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.download_file')
    def test_download_failure(self, mock_download):
        """Test handling of download failures"""
        # Arrange
        mock_download.side_effect = Exception("Download failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            process_transcribe_media(
                "http://test.com/audio.wav",
                "transcribe",
                include_text=True,
                include_srt=False,
                include_segments=False,
                word_timestamps=False,
                response_type="direct",
                language="en",
                job_id="test-123",
                words_per_line=None
            )
        assert "Download failed" in str(exc_info.value)
    
    @pytest.mark.unit
    @pytest.mark.asr
    @patch('services.v1.media.media_transcribe.ENABLE_FASTER_WHISPER', True)
    @patch('services.v1.media.media_transcribe.get_model')
    @patch('services.v1.media.media_transcribe.download_file')
    def test_transcription_failure(self, mock_download, mock_get_model):
        """Test handling of transcription failures"""
        # Arrange
        mock_download.return_value = "/tmp/test_audio.wav"
        mock_model = MagicMock()
        mock_get_model.return_value = mock_model
        
        mock_model.transcribe.side_effect = Exception("Transcription failed")
        
        # Act & Assert
        with patch('os.remove'):
            with pytest.raises(Exception) as exc_info:
                process_transcribe_media(
                    "http://test.com/audio.wav",
                    "transcribe",
                    include_text=True,
                    include_srt=False,
                    include_segments=False,
                    word_timestamps=False,
                    response_type="direct",
                    language="en",
                    job_id="test-123",
                    words_per_line=None
                )
            assert "Transcription failed" in str(exc_info.value)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
