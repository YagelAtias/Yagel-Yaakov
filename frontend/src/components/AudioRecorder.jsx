import React, { useState, useRef } from 'react';
import { BASE_URL } from '../api';

const AudioRecorder = ({ onAnalysisComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      // Disable browser audio filters because they heavily distort frequencies and confuse AI models.
      // Whisper works best with raw, uncompressed audio.
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
            noiseSuppression: false,
            echoCancellation: false,
            autoGainControl: false
        } 
      });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current.mimeType });
        await sendAudioToServer(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('לא ניתן לגשת למיקרופון');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Stop all audio tracks to release the mic
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const sendAudioToServer = async (blob) => {
    setLoading(true);
    const formData = new FormData();
    // Use .webm extension because browsers record in WebM (Opus) natively
    formData.append('file', blob, 'recording.webm');

    try {
      const response = await fetch(`${BASE_URL}/analyze_audio`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      onAnalysisComplete(data);
    } catch (error) {
      console.error('Error sending audio:', error);
      alert('שגיאה בשליחת האודיו לשרת');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '20px', padding: '15px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: '1rem', color: '#334155' }}>הקלטת שמע (ניתוח בזמן אמת)</h3>
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        {!isRecording ? (
          <button 
            onClick={startRecording} 
            disabled={loading}
            style={{ 
              background: '#ef4444', 
              color: 'white', 
              padding: '8px 16px', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: loading ? 'not-allowed' : 'pointer' 
            }}
          >
            {loading ? 'מנתח אודיו...' : '⏺ התחל הקלטה'}
          </button>
        ) : (
          <button 
            onClick={stopRecording}
            style={{ 
              background: '#1e293b', 
              color: 'white', 
              padding: '8px 16px', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              animation: 'pulse 1.5s infinite'
            }}
          >
            ⏹ עצור ונתח
          </button>
        )}
        {isRecording && <span style={{ color: '#ef4444', fontWeight: 'bold' }}>מקליט...</span>}
      </div>
    </div>
  );
};

export default AudioRecorder;
