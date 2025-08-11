"""
Test cases for startup and warm-up functionality.
"""

import os
import sys
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import startup


class TestStartup:
    """Test cases for startup module."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Reset the initialization status
        startup._initialization_status = {
            'model_loaded': False,
            'model_load_time': None,
            'model_error': None,
            'initialized_at': None,
        }
        
        # Clear environment variables
        os.environ.pop('ENABLE_MODEL_WARM_UP', None)
        os.environ.pop('ENABLE_FASTER_WHISPER', None)
    
    def test_warm_up_disabled(self):
        """Test warm-up when disabled."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'false'
        
        result = startup.warm_up_asr_model()
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'warm_up_disabled'
        assert 'disabled' in result['message'].lower()
    
    def test_warm_up_enabled_asr_disabled(self):
        """Test warm-up when enabled but ASR is disabled."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'false'
        
        result = startup.warm_up_asr_model()
        
        assert result['status'] == 'skipped'
        assert result['reason'] == 'asr_disabled'
        assert 'asr' in result['message'].lower()
    
    @patch('services.asr.get_model')
    def test_warm_up_success(self, mock_get_model):
        """Test successful warm-up."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        # Mock successful model loading
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        
        result = startup.warm_up_asr_model()
        
        assert result['status'] == 'success'
        assert result['model_loaded'] is True
        assert 'load_time' in result
        assert result['load_time'] >= 0
        
        # Check initialization status
        status = startup.get_initialization_status()
        assert status['model_loaded'] is True
        assert status['model_load_time'] is not None
        assert status['initialized_at'] is not None
    
    @patch('services.asr.get_model')
    def test_warm_up_model_returns_none(self, mock_get_model):
        """Test warm-up when model loader returns None."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        # Mock model loading returning None
        mock_get_model.return_value = None
        
        result = startup.warm_up_asr_model()
        
        assert result['status'] == 'partial'
        assert result['model_loaded'] is False
        assert 'error' in result
        
        # Check initialization status
        status = startup.get_initialization_status()
        assert status['model_loaded'] is False
        assert status['model_error'] is not None
    
    def test_warm_up_import_error(self):
        """Test warm-up when ASR module cannot be imported."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        with patch.dict('sys.modules', {'services.asr': None}):
            result = startup.warm_up_asr_model()
            
            assert result['status'] == 'error'
            assert result['model_loaded'] is False
            assert 'asr' in result['message'].lower()
    
    def test_is_ready_warm_up_disabled(self):
        """Test readiness check when warm-up is disabled."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'false'
        
        assert startup.is_ready() is True
    
    def test_is_ready_asr_disabled(self):
        """Test readiness check when ASR is disabled."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'false'
        
        assert startup.is_ready() is True
    
    def test_is_ready_model_not_loaded(self):
        """Test readiness check when model is not loaded."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        startup._initialization_status['model_loaded'] = False
        
        assert startup.is_ready() is False
    
    def test_is_ready_model_loaded(self):
        """Test readiness check when model is loaded."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        startup._initialization_status['model_loaded'] = True
        
        assert startup.is_ready() is True
    
    @patch('startup.warm_up_asr_model')
    def test_perform_startup_tasks(self, mock_warm_up):
        """Test perform_startup_tasks function."""
        # Test successful startup
        mock_warm_up.return_value = {
            'status': 'success',
            'model_loaded': True,
            'load_time': 1.5
        }
        
        result = startup.perform_startup_tasks()
        
        assert result['status'] == 'success'
        mock_warm_up.assert_called_once()
        
        # Test skipped startup
        mock_warm_up.reset_mock()
        mock_warm_up.return_value = {
            'status': 'skipped',
            'reason': 'warm_up_disabled'
        }
        
        result = startup.perform_startup_tasks()
        
        assert result['status'] == 'skipped'
        
        # Test failed startup
        mock_warm_up.reset_mock()
        mock_warm_up.return_value = {
            'status': 'error',
            'model_loaded': False,
            'error': 'Test error'
        }
        
        result = startup.perform_startup_tasks()
        
        assert result['status'] == 'error'


class TestHealthCheck:
    """Test cases for health check endpoint integration."""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from app import app
        with app.test_client() as client:
            yield client
    
    def setup_method(self):
        """Setup for each test method."""
        # Reset the initialization status
        startup._initialization_status = {
            'model_loaded': False,
            'model_load_time': None,
            'model_error': None,
            'initialized_at': None,
        }
        
        # Clear environment variables
        os.environ.pop('ENABLE_MODEL_WARM_UP', None)
        os.environ.pop('ENABLE_FASTER_WHISPER', None)
    
    def test_health_check_warm_up_disabled(self, client):
        """Test health check when warm-up is disabled."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'false'
        
        response = client.get('/health')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['status'] == 'healthy'
        assert data['ready'] is True
        assert data['configuration']['warm_up_enabled'] is False
    
    def test_health_check_model_loading(self, client):
        """Test health check when model is still loading."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        # Set model as not loaded
        startup._initialization_status['model_loaded'] = False
        
        response = client.get('/health')
        data = response.get_json()
        
        assert response.status_code == 503  # Service Unavailable
        assert data['status'] == 'starting'
        assert data['ready'] is False
        assert data['initialization']['model_loaded'] is False
    
    def test_health_check_model_loaded(self, client):
        """Test health check when model is loaded."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        # Set model as loaded
        startup._initialization_status['model_loaded'] = True
        startup._initialization_status['model_load_time'] = 2.5
        startup._initialization_status['initialized_at'] = time.time()
        
        response = client.get('/health')
        data = response.get_json()
        
        assert response.status_code == 200
        assert data['status'] == 'healthy'
        assert data['ready'] is True
        assert data['initialization']['model_loaded'] is True
        assert data['initialization']['model_load_time'] == 2.5
    
    def test_health_check_with_error(self, client):
        """Test health check when there was an error during warm-up."""
        os.environ['ENABLE_MODEL_WARM_UP'] = 'true'
        os.environ['ENABLE_FASTER_WHISPER'] = 'true'
        
        # Set error status
        startup._initialization_status['model_loaded'] = False
        startup._initialization_status['model_error'] = 'Failed to load model'
        
        response = client.get('/health')
        data = response.get_json()
        
        assert response.status_code == 503
        assert data['status'] == 'starting'
        assert data['ready'] is False
        assert 'error' in data['initialization']
        assert data['initialization']['error'] == 'Failed to load model'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
