# Copyright (c) 2025
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.



import os
import srt
from datetime import timedelta
from services.file_management import download_file
import logging
from config import LOCAL_STORAGE_PATH, ENABLE_OPENAI_WHISPER, ASR_MODEL_ID

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Helper function to map faster-whisper segment to OpenAI format
def _map_faster_whisper_segment(fw_segment):
    """Map a faster-whisper segment object to OpenAI Whisper format."""
    segment_dict = {
        'start': fw_segment.start,
        'end': fw_segment.end,
        'text': fw_segment.text,
    }
    
    # Map words if present
    if hasattr(fw_segment, 'words') and fw_segment.words:
        segment_dict['words'] = [
            {
                'start': word.start,
                'end': word.end,
                'word': word.word,
                'probability': getattr(word, 'probability', 1.0)
            }
            for word in fw_segment.words
        ]
    
    return segment_dict

# Helper function to transcribe using faster-whisper
def _transcribe_with_faster_whisper(model, audio_file, **kwargs):
    """Transcribe using faster-whisper and return OpenAI-compatible result."""
    # Extract parameters compatible with faster-whisper with optimized defaults
    fw_params = {
        'beam_size': kwargs.get('beam_size', 1),  # Reduced for speed (5 -> 1)
        'language': kwargs.get('language', None),
        'task': kwargs.get('task', 'transcribe'),
        'word_timestamps': kwargs.get('word_timestamps', False),
        # Performance optimizations
        'vad_filter': kwargs.get('vad_filter', True),  # Skip silent segments
        'vad_parameters': kwargs.get('vad_parameters', {
            'min_silence_duration_ms': 500,  # Minimum silence duration to split
            'speech_pad_ms': 400  # Padding around speech segments
        }),
        'temperature': kwargs.get('temperature', 0.0),  # Deterministic output for speed
        'compression_ratio_threshold': kwargs.get('compression_ratio_threshold', 2.4),  # Detect repetition
        'log_prob_threshold': kwargs.get('log_prob_threshold', -1.0),  # Quality threshold
        'no_speech_threshold': kwargs.get('no_speech_threshold', 0.6),  # Silence detection
        'condition_on_previous_text': kwargs.get('condition_on_previous_text', True),  # Context awareness
    }
    
    # Remove None values
    fw_params = {k: v for k, v in fw_params.items() if v is not None}
    
    # Log optimization settings for monitoring
    logger.info(f"Faster-Whisper optimizations: beam_size={fw_params['beam_size']}, vad_filter={fw_params.get('vad_filter')}, temperature={fw_params.get('temperature')}")
    
    # Transcribe with faster-whisper
    segments_generator, info = model.transcribe(audio_file, **fw_params)
    
    # Convert generator to list and map to OpenAI format
    segments = []
    text_parts = []
    
    for fw_segment in segments_generator:
        segment = _map_faster_whisper_segment(fw_segment)
        segments.append(segment)
        text_parts.append(segment['text'])
    
    # Build OpenAI-compatible result
    result = {
        'text': ''.join(text_parts),
        'segments': segments,
        'language': info.language if info else kwargs.get('language', 'en')
    }
    
    return result

def process_transcribe_media(media_url, task, include_text, include_srt, include_segments, word_timestamps, response_type, language, job_id, words_per_line=None):
    """Transcribe or translate media and return the transcript/translation, SRT or VTT file path."""
    logger.info(f"Starting {task} for media URL: {media_url}")
    input_filename = download_file(media_url, os.path.join(LOCAL_STORAGE_PATH, f"{job_id}_input"))
    logger.info(f"Downloaded media to local file: {input_filename}")

    try:
        # Faster-Whisper is now the default ASR backend
        from services.asr import get_model
        
        # Check if we should use legacy OpenAI Whisper
        if ENABLE_OPENAI_WHISPER:
            logger.info("Using legacy OpenAI Whisper model (ENABLE_OPENAI_WHISPER=true)")
            try:
                import whisper
                model = whisper.load_model(ASR_MODEL_ID.replace('openai/whisper-', ''))
                use_faster_whisper = False
                logger.info(f"Loaded OpenAI Whisper model: {ASR_MODEL_ID}")
            except ImportError:
                raise RuntimeError("OpenAI Whisper not installed but ENABLE_OPENAI_WHISPER=true")
        else:
            # Default: Use Faster-Whisper
            logger.info("Using Faster-Whisper model (default)")
            model = get_model()
            if not model:
                raise RuntimeError("Faster-Whisper model not available. Please install faster-whisper package.")
            use_faster_whisper = True
            logger.info(f"Loaded Faster-Whisper model: {ASR_MODEL_ID}")

        # Configure transcription/translation options
        options = {
            "task": task,
            "word_timestamps": word_timestamps,
            "verbose": False,
            "language": language
        }

        # Transcribe based on the selected model
        if use_faster_whisper:
            result = _transcribe_with_faster_whisper(model, input_filename, **options)
        else:
            # OpenAI Whisper uses a slightly different options format
            openai_options = {
                "task": task,
                "word_timestamps": word_timestamps,
                "verbose": False
            }
            if language:
                openai_options["language"] = language
            result = model.transcribe(input_filename, **openai_options)
        
        # For translation task, the result['text'] will be in English
        text = None
        srt_text = None
        segments_json = None

        logger.info(f"Generated {task} output")

        if include_text is True:
            text = result['text']

        if include_srt is True:
            srt_subtitles = []
            subtitle_index = 1
            
            if words_per_line and words_per_line > 0:
                # Collect all words and their timings
                all_words = []
                word_timings = []
                
                for segment in result['segments']:
                    words = segment['text'].strip().split()
                    segment_start = segment['start']
                    segment_end = segment['end']
                    
                    # Calculate timing for each word
                    if words:
                        duration_per_word = (segment_end - segment_start) / len(words)
                        for i, word in enumerate(words):
                            word_start = segment_start + (i * duration_per_word)
                            word_end = word_start + duration_per_word
                            all_words.append(word)
                            word_timings.append((word_start, word_end))
                
                # Process words in chunks of words_per_line
                current_word = 0
                while current_word < len(all_words):
                    # Get the next chunk of words
                    chunk = all_words[current_word:current_word + words_per_line]
                    
                    # Calculate timing for this chunk
                    chunk_start = word_timings[current_word][0]
                    chunk_end = word_timings[min(current_word + len(chunk) - 1, len(word_timings) - 1)][1]
                    
                    # Create the subtitle
                    srt_subtitles.append(srt.Subtitle(
                        subtitle_index,
                        timedelta(seconds=chunk_start),
                        timedelta(seconds=chunk_end),
                        ' '.join(chunk)
                    ))
                    subtitle_index += 1
                    current_word += words_per_line
            else:
                # Original behavior - one subtitle per segment
                for segment in result['segments']:
                    start = timedelta(seconds=segment['start'])
                    end = timedelta(seconds=segment['end'])
                    segment_text = segment['text'].strip()
                    srt_subtitles.append(srt.Subtitle(subtitle_index, start, end, segment_text))
                    subtitle_index += 1
            
            srt_text = srt.compose(srt_subtitles)

        if include_segments is True:
            segments_json = result['segments']

        os.remove(input_filename)
        logger.info(f"Removed local file: {input_filename}")
        logger.info(f"{task.capitalize()} successful, output type: {response_type}")

        if response_type == "direct":
            return text, srt_text, segments_json
        else:
            
            if include_text is True:
                text_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.txt")
                with open(text_filename, 'w') as f:
                    f.write(text)
            else:
                text_file = None
            
            if include_srt is True:
                srt_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.srt")
                with open(srt_filename, 'w') as f:
                    f.write(srt_text)
            else:
                srt_filename = None

            if include_segments is True:
                segments_filename = os.path.join(LOCAL_STORAGE_PATH, f"{job_id}.json")
                with open(segments_filename, 'w') as f:
                    f.write(str(segments_json))
            else:
                segments_filename = None

            return text_filename, srt_filename, segments_filename 

    except Exception as e:
        logger.error(f"{task.capitalize()} failed: {str(e)}")
        raise