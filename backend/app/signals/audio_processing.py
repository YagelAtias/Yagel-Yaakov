import os
import tempfile
import librosa
import numpy as np
from faster_whisper import WhisperModel

class AudioProcessor:
    def __init__(self):
        # Initialize the local Whisper model (tiny or base is fast enough for prototyping)
        # Using CPU for broad compatibility, but can be switched to CUDA later.
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")

    def process_audio(self, audio_bytes: bytes) -> dict:
        """
        Takes raw audio bytes, saves them to a volatile temporary file,
        uses Whisper to get word-level timestamps, and calculates the specific
        decibel level for the exact milliseconds each word was spoken.
        """
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")
        
        try:
            with os.fdopen(temp_fd, 'wb') as f:
                f.write(audio_bytes)

            # Load the audio using librosa to calculate global reference
            y, sr_librosa = librosa.load(temp_path, sr=None)
            
            if len(y) == 0:
                return {"status": "success", "segments": []}
                
            global_max = np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else 1.0
            
            # Transcribe with Whisper, requesting word-level timestamps
            segments_gen, _ = self.model.transcribe(temp_path, language="he", word_timestamps=True)
            
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
                            if avg_db > -15:
                                intensity = "shout"
                            elif avg_db < -35:
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
                if segment_max_intensity > -15:
                    overall_intensity = "shout"
                elif segment_max_intensity < -35:
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
