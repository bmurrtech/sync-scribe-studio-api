# tests/test_config_asr_profiles.py
import os
import sys
import importlib
import pytest


def load_config_with_env(monkeypatch):
    """Load config module with test API_KEY to avoid import-time error."""
    monkeypatch.setenv("API_KEY", "test")
    # Add parent directory to path for config import
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Ensure fresh import to re-evaluate module-level constants
    if "config" in sys.modules:
        del sys.modules["config"]
    return importlib.import_module("config")


def test_accuracy_turbo_profile_defaults(monkeypatch):
    """Test accuracy-turbo profile has hallucination/repetition mitigation settings."""
    cfg = load_config_with_env(monkeypatch)
    p = cfg.PROFILE_CONFIGS["accuracy-turbo"]
    
    # Hallucination/repetition mitigation settings
    assert p["vad_min_silence_ms"] == 700, "VAD silence should be 700ms for long-form"
    assert p["beam_size"] == 1, "Beam size should be 1 to prevent repetitive solutions"
    assert p["best_of"] == 1, "Best of should be 1 to prevent repetitive solutions"
    assert p["temperature"] == 0.2, "Temperature should be 0.2 for diversity"
    assert p["batch_size_gpu"] == 8, "GPU batch size should be reduced to 8 for long-form"
    
    # Sanity checks - unchanged keys
    assert p["model_id"] == "openai/whisper-large-v3-turbo"
    assert "description" in p


def test_accuracy_profile_defaults(monkeypatch):
    """Test accuracy profile has hallucination/repetition mitigation settings."""
    cfg = load_config_with_env(monkeypatch)
    p = cfg.PROFILE_CONFIGS["accuracy"]
    
    # Hallucination/repetition mitigation settings
    assert p["vad_min_silence_ms"] == 900, "VAD silence should be 900ms for conservative long-form"
    assert p["beam_size"] == 1, "Beam size should be 1 to prevent repetitive solutions"
    assert p["best_of"] == 1, "Best of should be 1 to prevent repetitive solutions"
    assert p["temperature"] == 0.2, "Temperature should be 0.2 for diversity"
    assert p["batch_size_gpu"] == 4, "GPU batch size should be reduced to 4 for large model"
    
    # Sanity checks - unchanged keys
    assert p["model_id"] == "openai/whisper-large-v3"
    assert "description" in p


def test_other_profiles_unchanged(monkeypatch):
    """Ensure speed and balanced profiles are not affected by the changes."""
    cfg = load_config_with_env(monkeypatch)
    
    speed_profile = cfg.PROFILE_CONFIGS["speed"]
    assert speed_profile["vad_min_silence_ms"] == 300
    assert speed_profile["beam_size"] == 1
    assert speed_profile["temperature"] == 0.0
    
    balanced_profile = cfg.PROFILE_CONFIGS["balanced"]
    assert balanced_profile["vad_min_silence_ms"] == 400
    assert balanced_profile["beam_size"] == 2
    assert balanced_profile["temperature"] == 0.0
