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
import uuid
from config import ENABLE_OPENAI_WHISPER

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Set the default local storage directory
STORAGE_PATH = "/tmp/"

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
    # Extract parameters compatible with faster-whisper
    fw_params = {
        'beam_size': kwargs.get('beam_size', 5),
        'language': kwargs.get('language', None),
        'task': kwargs.get('task', 'transcribe'),
        'word_timestamps': kwargs.get('word_timestamps', False),
    }
    
    # Remove None values
    fw_params = {k: v for k, v in fw_params.items() if v is not None}
    
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

def process_transcription(media_url, output_type, max_chars=56, language=None,):
    """Transcribe media and return the transcript, SRT or ASS file path."""
    logger.info(f"Starting transcription for media URL: {media_url} with output type: {output_type}")
    input_filename = download_file(media_url, os.path.join(STORAGE_PATH, 'input_media'))
    logger.info(f"Downloaded media to local file: {input_filename}")

    try:
        # Faster-Whisper is now the default ASR backend
        from services.asr import get_model
        from config import ASR_MODEL_ID
        
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

        # Transcribe based on output type
        if output_type == 'transcript':
            if use_faster_whisper:
                result = _transcribe_with_faster_whisper(model, input_filename, language=language)
            else:
                result = model.transcribe(input_filename, language=language)
            output = result['text']
            logger.info("Generated transcript output")
        elif output_type in ['srt', 'vtt']:
            if use_faster_whisper:
                result = _transcribe_with_faster_whisper(model, input_filename, language=language)
            else:
                result = model.transcribe(input_filename, language=language)
            
            srt_subtitles = []
            for i, segment in enumerate(result['segments'], start=1):
                start = timedelta(seconds=segment['start'])
                end = timedelta(seconds=segment['end'])
                text = segment['text'].strip()
                srt_subtitles.append(srt.Subtitle(i, start, end, text))
            
            output_content = srt.compose(srt_subtitles)
            
            # Write the output to a file
            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w') as f:
                f.write(output_content)
            
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")

        elif output_type == 'ass':
            if use_faster_whisper:
                result = _transcribe_with_faster_whisper(
                    model, 
                    input_filename,
                    word_timestamps=True,
                    task='transcribe',
                    language=language
                )
            else:
                result = model.transcribe(
                    input_filename,
                    word_timestamps=True,
                    task='transcribe',
                    verbose=False,
                    language=language
                )
            logger.info("Transcription completed with word-level timestamps")
            # Generate ASS subtitle content
            ass_content = generate_ass_subtitle(result, max_chars)
            logger.info("Generated ASS subtitle content")
            
            output_content = ass_content

            # Write the ASS content to a file
            output_filename = os.path.join(STORAGE_PATH, f"{uuid.uuid4()}.{output_type}")
            with open(output_filename, 'w') as f:
               f.write(output_content) 
            output = output_filename
            logger.info(f"Generated {output_type.upper()} output: {output}")
        else:
            raise ValueError("Invalid output type. Must be 'transcript', 'srt', or 'vtt'.")

        os.remove(input_filename)
        logger.info(f"Removed local file: {input_filename}")
        logger.info(f"Transcription successful, output type: {output_type}")
        return output
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise


def generate_ass_subtitle(result, max_chars):
    """Generate ASS subtitle content with highlighted current words, showing one line at a time."""
    logger.info("Generate ASS subtitle content with highlighted current words")
    # ASS file header
    ass_content = ""

    # Helper function to format time
    def format_time(t):
        hours = int(t // 3600)
        minutes = int((t % 3600) // 60)
        seconds = int(t % 60)
        centiseconds = int(round((t - int(t)) * 100))
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    max_chars_per_line = max_chars  # Maximum characters per line

    # Process each segment
    for segment in result['segments']:
        words = segment.get('words', [])
        if not words:
            continue  # Skip if no word-level timestamps

        # Group words into lines
        lines = []
        current_line = []
        current_line_length = 0
        for word_info in words:
            word_length = len(word_info['word']) + 1  # +1 for space
            if current_line_length + word_length > max_chars_per_line:
                lines.append(current_line)
                current_line = [word_info]
                current_line_length = word_length
            else:
                current_line.append(word_info)
                current_line_length += word_length
        if current_line:
            lines.append(current_line)

        # Generate events for each line
        for line in lines:
            line_start_time = line[0]['start']
            line_end_time = line[-1]['end']

            # Generate events for highlighting each word
            for i, word_info in enumerate(line):
                start_time = word_info['start']
                end_time = word_info['end']
                current_word = word_info['word']

                # Build the line text with highlighted current word
                caption_parts = []
                for w in line:
                    word_text = w['word']
                    if w == word_info:
                        # Highlight current word
                        caption_parts.append(r'{\c&H00FFFF&}' + word_text)
                    else:
                        # Default color
                        caption_parts.append(r'{\c&HFFFFFF&}' + word_text)
                caption_with_highlight = ' '.join(caption_parts)

                # Format times
                start = format_time(start_time)
                # End the dialogue event when the next word starts or at the end of the line
                if i + 1 < len(line):
                    end_time = line[i + 1]['start']
                else:
                    end_time = line_end_time
                end = format_time(end_time)

                # Add the dialogue line
                ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{caption_with_highlight}\n"

    return ass_content