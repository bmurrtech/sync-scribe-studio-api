"""
Integration tests for ASR with real audio file.
Tests the complete flow with actual WAV file and both model backends.
"""

import pytest
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestASRIntegration:
    """Integration tests for ASR transcription with real audio"""
    
    @pytest.fixture
    def test_wav_path(self):
        """Get path to test WAV file"""
        return Path(__file__).parent.parent / "fixtures" / "test_audio.wav"
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API testing"""
        return os.getenv("LOCAL_BASE_URL", "http://localhost:8080")
    
    @pytest.fixture
    def api_key(self):
        """API key for testing"""
        return os.getenv("API_KEY", "test-api-key")
    
    @pytest.mark.integration
    @pytest.mark.asr
    def test_transcribe_endpoint_with_real_audio(self, base_url, api_key, test_wav_path):
        """Test /v1/media/transcribe endpoint with real audio file"""
        if not test_wav_path.exists():
            pytest.skip(f"Test WAV file not found: {test_wav_path}")
        
        # Upload the test file to a temporary location (mock URL for testing)
        # In a real test, you'd upload to a test bucket
        test_url = f"file://{test_wav_path}"
        
        # Test with both model backends
        for enable_faster in [True, False]:
            with patch.dict(os.environ, {"ENABLE_FASTER_WHISPER": str(enable_faster).lower()}):
                response = requests.post(
                    f"{base_url}/v1/media/transcribe",
                    headers={"X-API-Key": api_key},
                    json={
                        "media_url": test_url,
                        "task": "transcribe",
                        "include_text": True,
                        "include_srt": True,
                        "include_segments": True,
                        "word_timestamps": False
                    },
                    timeout=30
                )
                
                # Check response structure
                assert response.status_code in [200, 202]
                data = response.json()
                
                if response.status_code == 202:
                    # Async response - check for job_id
                    assert "job_id" in data
                    assert "message" in data
                else:
                    # Sync response - check for results
                    assert "response" in data or "result" in data
                    result = data.get("response") or data.get("result")
                    
                    if result:
                        # Check that we have the expected fields
                        if "text" in result:
                            assert isinstance(result["text"], str)
                        if "srt" in result:
                            assert isinstance(result["srt"], str)
                        if "segments" in result:
                            assert isinstance(result["segments"], list)
    
    @pytest.mark.integration
    @pytest.mark.asr
    @patch.dict(os.environ, {"ENABLE_FASTER_WHISPER": "true"})
    def test_consistent_output_between_models(self, test_wav_path):
        """Test that both models produce consistent output structure"""
        if not test_wav_path.exists():
            pytest.skip(f"Test WAV file not found: {test_wav_path}")
        
        from services.v1.media.media_transcribe import process_transcribe_media
        
        results = {}
        
        # Test with faster-whisper
        with patch.dict(os.environ, {"ENABLE_FASTER_WHISPER": "true"}):
            with patch('services.v1.media.media_transcribe.download_file') as mock_download:
                mock_download.return_value = str(test_wav_path)
                
                try:
                    with patch('os.remove'):
                        result_fw = process_transcribe_media(
                            "http://test.com/audio.wav",
                            "transcribe",
                            include_text=True,
                            include_srt=True,
                            include_segments=True,
                            word_timestamps=False,
                            response_type="direct",
                            language="en",
                            job_id="test-fw",
                            words_per_line=None
                        )
                    results['faster_whisper'] = result_fw
                except Exception as e:
                    pytest.skip(f"Faster-whisper not available: {e}")
        
        # Test with OpenAI Whisper
        with patch.dict(os.environ, {"ENABLE_FASTER_WHISPER": "false"}):
            with patch('services.v1.media.media_transcribe.download_file') as mock_download:
                mock_download.return_value = str(test_wav_path)
                
                try:
                    with patch('os.remove'):
                        result_ow = process_transcribe_media(
                            "http://test.com/audio.wav",
                            "transcribe",
                            include_text=True,
                            include_srt=True,
                            include_segments=True,
                            word_timestamps=False,
                            response_type="direct",
                            language="en",
                            job_id="test-ow",
                            words_per_line=None
                        )
                    results['openai_whisper'] = result_ow
                except Exception as e:
                    pytest.skip(f"OpenAI Whisper not available: {e}")
        
        if len(results) == 2:
            # Compare output structure (not exact content as models may differ slightly)
            fw_text, fw_srt, fw_segments = results['faster_whisper']
            ow_text, ow_srt, ow_segments = results['openai_whisper']
            
            # Check that both return the same types
            assert type(fw_text) == type(ow_text)
            assert type(fw_srt) == type(ow_srt)
            assert type(fw_segments) == type(ow_segments)
            
            # Check that segments have similar structure
            if fw_segments and ow_segments:
                assert isinstance(fw_segments, list)
                assert isinstance(ow_segments, list)
                
                if len(fw_segments) > 0 and len(ow_segments) > 0:
                    # Check first segment structure
                    fw_seg = fw_segments[0]
                    ow_seg = ow_segments[0]
                    
                    assert 'start' in fw_seg and 'start' in ow_seg
                    assert 'end' in fw_seg and 'end' in ow_seg
                    assert 'text' in fw_seg and 'text' in ow_seg
    
    @pytest.mark.integration
    @pytest.mark.asr
    def test_srt_generation_formats(self, test_wav_path):
        """Test that SRT generation produces valid SRT format"""
        if not test_wav_path.exists():
            pytest.skip(f"Test WAV file not found: {test_wav_path}")
        
        from services.v1.media.media_transcribe import process_transcribe_media
        
        with patch('services.v1.media.media_transcribe.download_file') as mock_download:
            mock_download.return_value = str(test_wav_path)
            
            try:
                with patch('os.remove'):
                    _, srt_content, _ = process_transcribe_media(
                        "http://test.com/audio.wav",
                        "transcribe",
                        include_text=False,
                        include_srt=True,
                        include_segments=False,
                        word_timestamps=False,
                        response_type="direct",
                        language="en",
                        job_id="test-srt",
                        words_per_line=None
                    )
                
                if srt_content:
                    # Validate SRT format
                    lines = srt_content.strip().split('\n')
                    assert len(lines) > 0
                    
                    # Check for SRT structure (number, timestamp, text)
                    i = 0
                    while i < len(lines):
                        if lines[i].strip():
                            # Should be a number
                            assert lines[i].strip().isdigit(), f"Expected number, got: {lines[i]}"
                            i += 1
                            
                            # Should be timestamp
                            if i < len(lines):
                                assert '-->' in lines[i], f"Expected timestamp, got: {lines[i]}"
                                i += 1
                            
                            # Should be text (can be multiple lines)
                            if i < len(lines) and lines[i].strip():
                                i += 1
                                # Skip any additional text lines
                                while i < len(lines) and lines[i].strip() and not lines[i].strip().isdigit():
                                    i += 1
                        else:
                            i += 1
            except ImportError:
                pytest.skip("ASR models not available")
    
    @pytest.mark.integration
    @pytest.mark.asr
    def test_words_per_line_functionality(self, test_wav_path):
        """Test that words_per_line parameter correctly splits subtitles"""
        if not test_wav_path.exists():
            pytest.skip(f"Test WAV file not found: {test_wav_path}")
        
        from services.v1.media.media_transcribe import process_transcribe_media
        
        with patch('services.v1.media.media_transcribe.download_file') as mock_download:
            mock_download.return_value = str(test_wav_path)
            
            try:
                # Test with different words_per_line values
                for wpl in [1, 3, 5]:
                    with patch('os.remove'):
                        _, srt_content, _ = process_transcribe_media(
                            "http://test.com/audio.wav",
                            "transcribe",
                            include_text=False,
                            include_srt=True,
                            include_segments=False,
                            word_timestamps=False,
                            response_type="direct",
                            language="en",
                            job_id=f"test-wpl-{wpl}",
                            words_per_line=wpl
                        )
                    
                    if srt_content:
                        # Check that subtitle lines respect words_per_line
                        lines = srt_content.strip().split('\n')
                        for line in lines:
                            if line.strip() and not line.strip().isdigit() and '-->' not in line:
                                # This is a subtitle text line
                                words = line.strip().split()
                                # Should have at most wpl words (may have less at end)
                                assert len(words) <= wpl, f"Line has {len(words)} words, expected max {wpl}: {line}"
            except ImportError:
                pytest.skip("ASR models not available")


class TestASRPerformance:
    """Performance tests for ASR functionality"""
    
    @pytest.mark.performance
    @pytest.mark.asr
    def test_model_loading_performance(self):
        """Test that model loading is reasonably fast"""
        from services.asr import get_model, unload_model
        
        # Unload any existing model
        unload_model()
        
        # Time model loading
        start_time = time.time()
        model = get_model()
        load_time = time.time() - start_time
        
        if model:
            # Model loading should be under 30 seconds (generous for CI)
            assert load_time < 30, f"Model loading took {load_time:.2f} seconds"
            
            # Second load should be instant (cached)
            start_time = time.time()
            model2 = get_model()
            cached_time = time.time() - start_time
            
            assert cached_time < 0.1, f"Cached model loading took {cached_time:.2f} seconds"
            assert model is model2, "Should return same model instance"
            
            # Clean up
            unload_model()
    
    @pytest.mark.performance
    @pytest.mark.asr
    def test_transcription_performance(self, test_wav_path):
        """Test that transcription is reasonably fast for small files"""
        if not test_wav_path.exists():
            pytest.skip(f"Test WAV file not found: {test_wav_path}")
        
        from services.v1.media.media_transcribe import process_transcribe_media
        
        with patch('services.v1.media.media_transcribe.download_file') as mock_download:
            mock_download.return_value = str(test_wav_path)
            
            try:
                start_time = time.time()
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
                        job_id="test-perf",
                        words_per_line=None
                    )
                transcribe_time = time.time() - start_time
                
                # For a 2-second audio file, transcription should be under 10 seconds
                assert transcribe_time < 10, f"Transcription took {transcribe_time:.2f} seconds"
            except ImportError:
                pytest.skip("ASR models not available")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration or asr"])
