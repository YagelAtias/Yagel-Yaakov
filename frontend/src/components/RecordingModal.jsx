import React, { useState, useEffect, useRef } from 'react';
import { secureFetch } from '../api';
import './TeacherDashboard.css';

export default function RecordingModal({ studentId, studentName, onClose, onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [liveText, setLiveText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [devices, setDevices] = useState([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState("");
  const [volume, setVolume] = useState(0);
  const [transcriptionPhase, setTranscriptionPhase] = useState("recording"); // "recording", "transcribing", "reviewing"
  const [finalSegments, setFinalSegments] = useState([]);
  const [editableText, setEditableText] = useState("");
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const rafIdRef = useRef(null);

  useEffect(() => {
    async function initDevices() {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        const allDevices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = allDevices.filter(d => d.kind === 'audioinput');
        setDevices(audioInputs);
        if (audioInputs.length > 0) {
          setSelectedDeviceId(audioInputs[0].deviceId); 
        } else {
          setError("לא נמצא מיקרופון מחובר.");
        }
      } catch (err) {
        setError("שגיאה בגישה למיקרופון: " + err.message);
      }
    }
    initDevices();

    return () => {
      stopRecordingCleanup();
    };
  }, []);

  useEffect(() => {
    if (selectedDeviceId) {
      startRecording(selectedDeviceId);
    }
  }, [selectedDeviceId]);

  const startRecording = async (deviceId) => {
    stopRecordingCleanup();
    setError(null);
    audioChunksRef.current = [];
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { 
          deviceId: deviceId ? { exact: deviceId } : undefined,
          autoGainControl: false,
          noiseSuppression: false,
          echoCancellation: true
        } 
      });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      
      // Setup Audio Analyzer for volume meter
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);
      analyser.fftSize = 256;
      
      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const updateVolume = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for(let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const average = sum / bufferLength;
        setVolume(Math.min(100, Math.round((average / 255) * 100 * 2.5))); 
        rafIdRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();
      
      setIsRecording(true);
      setIsPaused(false);
    } catch (err) {
      setError("שגיאה בהפעלת מיקרופון: " + err.message);
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "paused") {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
    }
  };

  const stopRecordingCleanup = () => {
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch(e) {}
    }
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      // Temporarily remove onstop to prevent finishAndAnalyze from firing if cancelled
      mediaRecorderRef.current.onstop = null; 
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    setVolume(0);
  };

  const finishAndTranscribe = async () => {
    if (!mediaRecorderRef.current) return;
    setTranscriptionPhase("transcribing");

    // Wait for the final chunk to be appended via onstop
    mediaRecorderRef.current.onstop = async () => {
      // Ensure all tracks are stopped
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.webm');
      formData.append('student_id', studentId);

      try {
        const response = await secureFetch('/transcribe_audio', {
          method: 'POST',
          body: formData
        });
        
        if (response.status === "error") {
            setError('שגיאה מהשרת: ' + response.error);
            setTranscriptionPhase("recording");
            return;
        }

        const segments = response.segments || [];
        setFinalSegments(segments);
        const fullText = segments.map(s => s.text).join(" ");
        setEditableText(fullText);
        setTranscriptionPhase("reviewing");
      } catch (err) {
        setError('שגיאה בשמירת התמלול: ' + err.message);
        setTranscriptionPhase("recording");
      }
    };

    // Trigger the stop event
    mediaRecorderRef.current.stop();
    if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch(e) {}
    }
  };

  const handleFinalSubmit = async () => {
    setTranscriptionPhase("transcribing"); // Reuse loading state visually
    try {
      const originalText = finalSegments.map(s => s.text).join(" ");
      const payload = {
        student_id: studentId,
        segments: finalSegments,
        text: editableText,
        text_was_edited: (editableText !== originalText)
      };
      
      await secureFetch('/analyze_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      alert('השיחה נותחה ונשמרה בארכיון בהצלחה!');
      onRecordingComplete(); 
    } catch(err) {
      setError('שגיאה בניתוח התמלול: ' + err.message);
      setTranscriptionPhase("reviewing");
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 1500, direction: 'rtl'
    }}>
      <div style={{
        backgroundColor: '#fff', padding: '30px', borderRadius: '16px', width: '90%', maxWidth: '600px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)', textAlign: 'center'
      }}>
        <h2 style={{ margin: '0 0 15px 0', color: '#00838f' }}>תמלול שיחה פעיל</h2>
        <h4 style={{ margin: '0 0 25px 0', color: '#546e7a', fontWeight: 'normal' }}>תלמיד: <strong>{studentName}</strong></h4>

        {error ? (
          <div style={{ color: '#d32f2f', marginBottom: '20px', padding: '10px', backgroundColor: '#ffebee', borderRadius: '8px' }}>
            {error}
          </div>
        ) : transcriptionPhase === "reviewing" ? (
          <>
            <h4 style={{ color: '#333', marginBottom: '10px' }}>ערוך וקורא את התמלול לפני השמירה:</h4>
            <textarea 
              value={editableText}
              onChange={(e) => setEditableText(e.target.value)}
              style={{
                width: '100%', height: '150px', padding: '10px', borderRadius: '8px', 
                border: '1px solid #00838f', fontSize: '1.1rem', resize: 'vertical',
                marginBottom: '20px', fontFamily: 'inherit'
              }}
            />
            <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
              <button 
                onClick={handleFinalSubmit}
                style={{ padding: '12px 24px', fontSize: '1.1rem', borderRadius: '8px', border: 'none', backgroundColor: '#d32f2f', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
              >
                💾 שמור יומן ונתח מצוקה
              </button>
            </div>
          </>
        ) : (
          <>
            {/* Microphone Selector */}
            {devices.length > 0 && (
              <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <label style={{ fontSize: '0.9rem', color: '#546e7a' }}>בחר מיקרופון:</label>
                <select 
                  value={selectedDeviceId}
                  onChange={(e) => setSelectedDeviceId(e.target.value)}
                  style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid #cfd8dc', fontSize: '0.9rem', maxWidth: '250px' }}
                >
                  {devices.map(d => (
                    <option key={d.deviceId} value={d.deviceId}>{d.label || `מיקרופון (${d.deviceId.slice(0,5)}...)`}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Visual Indicator */}
            <div style={{ 
              height: '100px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: '20px' 
            }}>
              {transcriptionPhase === "transcribing" ? (
                <div style={{ color: '#ff9800', fontWeight: 'bold', fontSize: '1.2rem' }}>
                  ⏳ ממתין לסיום עיבוד והפקת תמלול...
                </div>
              ) : (
                <>
                  <div style={{ 
                    width: '60px', height: '60px', borderRadius: '50%', 
                    backgroundColor: isPaused ? '#9e9e9e' : '#f44336',
                    animation: (!isPaused && isRecording && volume > 5) ? 'pulse 1.5s infinite' : 'none',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '1.5rem',
                    marginBottom: '10px'
                  }}>
                    {isPaused ? '⏸️' : '🎙️'}
                  </div>
                  {/* Volume Bar */}
                  <div style={{ width: '150px', height: '8px', backgroundColor: '#e0e0e0', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ 
                      height: '100%', width: `${isPaused ? 0 : volume}%`, 
                      backgroundColor: volume > 80 ? '#f44336' : volume > 50 ? '#ff9800' : '#4caf50',
                      transition: 'width 0.1s, background-color 0.2s'
                    }}></div>
                  </div>
                </>
              )}
            </div>

            {/* Controls */}
            {transcriptionPhase === "recording" && (
              <div style={{ display: 'flex', gap: '15px', justifyContent: 'center' }}>
                {isPaused ? (
                  <button 
                    onClick={resumeRecording}
                    style={{ padding: '12px 24px', fontSize: '1.1rem', borderRadius: '8px', border: 'none', backgroundColor: '#00897b', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    ▶️ המשך שיחה
                  </button>
                ) : (
                  <button 
                    onClick={pauseRecording}
                    style={{ padding: '12px 24px', fontSize: '1.1rem', borderRadius: '8px', border: 'none', backgroundColor: '#ff9800', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    ⏸️ השהה
                  </button>
                )}

                <button 
                  onClick={finishAndTranscribe}
                  style={{ padding: '12px 24px', fontSize: '1.1rem', borderRadius: '8px', border: 'none', backgroundColor: '#d32f2f', color: '#fff', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  ⏹️ סיים הקלטה
                </button>
              </div>
            )}
            
            {transcriptionPhase === "recording" && (
              <button 
                onClick={onClose}
                style={{ marginTop: '20px', padding: '8px 16px', fontSize: '0.9rem', borderRadius: '8px', border: '1px solid #9e9e9e', backgroundColor: 'transparent', color: '#616161', cursor: 'pointer' }}
              >
                ביטול
              </button>
            )}
          </>
        )}
      </div>
      <style>{`
        @keyframes pulse {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(244, 67, 54, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
        }
      `}</style>
    </div>
  );
}
