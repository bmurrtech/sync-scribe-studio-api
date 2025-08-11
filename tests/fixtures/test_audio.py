#!/usr/bin/env python3
"""
Generate test audio file for ASR testing.
Creates a short WAV file with synthesized speech or tones.
"""

import numpy as np
import wave
import os
from pathlib import Path

def generate_test_wav(output_path: str, duration: float = 2.0, sample_rate: int = 16000):
    """
    Generate a test WAV file with a tone that simulates speech.
    
    Args:
        output_path: Path where the WAV file will be saved
        duration: Duration in seconds
        sample_rate: Sample rate in Hz (16000 is standard for speech)
    """
    # Create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate a mix of frequencies that somewhat resembles speech
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Mix of frequencies (simulating vowel formants)
    f1, f2, f3 = 700, 1220, 2600  # Formant frequencies for 'a' sound
    signal = (
        0.3 * np.sin(2 * np.pi * f1 * t) +
        0.3 * np.sin(2 * np.pi * f2 * t) +
        0.2 * np.sin(2 * np.pi * f3 * t)
    )
    
    # Add some amplitude modulation to simulate speech rhythm
    modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 3 * t)  # 3 Hz modulation
    signal = signal * modulation
    
    # Add small amount of noise
    noise = np.random.normal(0, 0.01, len(signal))
    signal = signal + noise
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal))
    
    # Convert to 16-bit PCM
    signal_int16 = np.int16(signal * 32767)
    
    # Write WAV file
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal_int16.tobytes())
    
    print(f"Generated test WAV file: {output_path}")
    print(f"  Duration: {duration} seconds")
    print(f"  Sample rate: {sample_rate} Hz")
    print(f"  Size: {os.path.getsize(output_path)} bytes")
    
    return output_path

if __name__ == "__main__":
    # Generate test audio file
    fixtures_dir = Path(__file__).parent
    test_wav_path = fixtures_dir / "test_audio.wav"
    generate_test_wav(str(test_wav_path))
