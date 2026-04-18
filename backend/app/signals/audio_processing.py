import os
import tempfile
import librosa
import numpy as np
from faster_whisper import WhisperModel
import imageio_ffmpeg

# Ensure ffmpeg is in the PATH and named correctly for faster-whisper
_ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
_ffmpeg_dir = os.path.dirname(_ffmpeg_exe)
_ffmpeg_alias = os.path.join(_ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(_ffmpeg_alias):
    import shutil
    shutil.copy(_ffmpeg_exe, _ffmpeg_alias)
os.environ["PATH"] += os.pathsep + _ffmpeg_dir

class AudioProcessor:
    def __init__(self):
        # Initialize the local Whisper model
        # Using the state-of-the-art "turbo" model (Whisper large-v3-turbo).
        # It is as accurate as the massive "large" model but optimized to run 8x faster on CPUs.
        self.model = WhisperModel("turbo", device="cpu", compute_type="int8")

    def process_audio(self, audio_bytes: bytes) -> dict:
        """
        Takes raw audio bytes, saves them to a volatile temporary file,
        uses Whisper to get word-level timestamps, and calculates the specific
        decibel level for the exact milliseconds each word was spoken.
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix=".webm")
        
        try:
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(audio_bytes)

            # Load the audio using librosa to calculate global reference
            y, sr_librosa = librosa.load(temp_path, sr=None)
            
            if len(y) == 0:
                return {"status": "success", "segments": []}
                
            global_max = np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else 1.0
            
            # Transcribe with Whisper, requesting word-level timestamps
            # Enable VAD (Voice Activity Detection) to stop the AI from hallucinating 
            # sentences like "תודה רבה" (Thanks for watching) during background noise/silence.
            segments_gen, _ = self.model.transcribe(
                temp_path, 
                language="he", 
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False
            )
            
            structured_segments = []
            
            for segment in segments_gen:
                segment_words = []
                segment_max_intensity = -100
                
                if not segment.words:
                    continue

                for word in segment.words:
                    # Whisper gives start and end in seconds
                    start_sec = word.start
                    end_sec = word.end
                    
                    # Convert seconds to librosa array indices
                    start_idx = int(start_sec * sr_librosa)
                    end_idx = int(end_sec * sr_librosa)
                    
                    # Prevent out of bounds
                    end_idx = min(end_idx, len(y))
                    
                    chunk_y = y[start_idx:end_idx]
                    
                    if len(chunk_y) == 0:
                        intensity = "normal"
                    else:
                        rms = librosa.feature.rms(y=chunk_y)[0]
                        if len(rms) == 0 or np.max(rms) == 0:
                            intensity = "normal"
                        else:
                            db_values = librosa.amplitude_to_db(rms, ref=global_max)
                            avg_db = np.mean(db_values)
                            segment_max_intensity = max(segment_max_intensity, avg_db)
                            
                            # Map relative dB to whisper, normal, shout.
                            # Adjusted thresholds since we turned off browser AutoGainControl.
                            # RMS values are typically 12-15dB lower than peak, so -20dB is a solid shout.
                            if avg_db > -20:
                                intensity = "shout"
                            elif avg_db < -40:
                                intensity = "whisper"
                            else:
                                intensity = "normal"
                                
                    clean_word = word.word.strip()
                    if clean_word:
                        segment_words.append({
                            "word": clean_word,
                            "intensity": intensity
                        })
                
                # Determine overall segment intensity for backwards compatibility / UI coloring
                overall_intensity = "normal"
                if segment_max_intensity > -20:
                    overall_intensity = "shout"
                elif segment_max_intensity < -40:
                    overall_intensity = "whisper"
                    
                structured_segments.append({
                    "text": segment.text.strip(),
                    "intensity": overall_intensity,
                    "words": segment_words
                })

            return {
                "status": "success",
                "segments": structured_segments
            }

        except Exception as e:
            print(f"Error processing audio: {e}")
            return {"status": "error", "error": str(e)}
            
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
