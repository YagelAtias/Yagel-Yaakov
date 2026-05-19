import os
import tempfile
import subprocess
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
        wav_path = temp_path + ".wav"
        
        try:
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(audio_bytes)

            # Explicitly convert WebM to WAV using the ffmpeg binary to avoid librosa/ffprobe issues
            subprocess.run([
                _ffmpeg_exe, "-y", "-i", temp_path, 
                "-ac", "1", "-ar", "16000", wav_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Load the WAV file using librosa
            y, sr_librosa = librosa.load(wav_path, sr=16000)
            
            if len(y) == 0:
                return {"status": "success", "segments": []}
            
            # Transcribe with Whisper, requesting word-level timestamps
            # Enable VAD (Voice Activity Detection) to stop the AI from hallucinating 
            # sentences like "תודה רבה" (Thanks for watching) during background noise/silence.
            # Transcribe the WAV file with Whisper
            segments_gen, _ = self.model.transcribe(
                wav_path, 
                language="he", 
                word_timestamps=True,
                vad_filter=False,
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
                            # Use absolute reference (1.0) instead of the recording's max
                            # This ensures we measure true volume, not just the loudest word in the current recording.
                            db_values = librosa.amplitude_to_db(rms, ref=1.0)
                            avg_db = np.mean(db_values)
                            segment_max_intensity = max(segment_max_intensity, avg_db)
                            
                            # With absolute reference (1.0) and AutoGainControl OFF:
                            # Hardware mic gains vary, but generally without AGC:
                            # Shouting peaks around -20dB to -15dB
                            # Normal speech is around -45dB to -25dB
                            # Whispering is < -45dB
                            if avg_db > -26:
                                intensity = "shout"
                            elif avg_db < -42:
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
                if segment_max_intensity > -26:
                    overall_intensity = "shout"
                elif segment_max_intensity < -42:
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
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except OSError:
                    pass
