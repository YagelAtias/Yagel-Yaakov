import { useState } from 'react'
import './App.css'
// Custom components
import AcousticControl from './components/AcousticControl'
import AnalysisResult from './components/AnalysisResult'
import SegmentedEditor from './components/SegmentedEditor'

function App() {
  const [useSegments, setUseSegments] = useState(false)
  const [segments, setSegments] = useState([])
  const [text, setText] = useState('')
  const [decibels, setDecibels] = useState(60)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const analyzeDistress = async () => {
    setError('')
    if (useSegments) {
      const hasText = segments.some(s => (s.text || '').trim().length > 0)
      if (!hasText) {
        setError('נא להוסיף לפחות מקטע אחד עם טקסט')
        return
      }
    } else {
      if (!text) {
        setError('נא להזין טקסט לניתוח')
        return
      }
    }

    setLoading(true)
    try {
      const payload = useSegments
        ? { segments: segments }
        : { text: text, avg_decibels: parseFloat(decibels) }

      const response = await fetch('http://127.0.0.1:8000/api/v2/analyze_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Connection error:', error)
      setError('שגיאת תקשורת לשרת')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container" dir="rtl">
      <h1>מעבדת ניתוח אותות</h1>

      <div className="input-card">
        <div className="toggle-row">
          <label className="label">מצב מקטעים (משפטים)</label>
          <input
            type="checkbox"
            checked={useSegments}
            onChange={(e) => setUseSegments(e.target.checked)}
          />
        </div>

        {!useSegments && (
          <>
            <label className="label">הכנס טקסט לניתוח כאן:</label>
            <textarea
              className="text-input"
              rows="4"
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <AcousticControl decibels={decibels} setDecibels={setDecibels} />
          </>
        )}

        {useSegments && (
          <SegmentedEditor segments={segments} setSegments={setSegments} />
        )}

        {error && <div style={{ color: '#f87171', marginTop: 8 }}>{error}</div>}

        <button className="analyze-btn" onClick={analyzeDistress} disabled={loading}>
          {loading ? 'מחשב תוצאה משוקללת...' : 'בצע ניתוח'}
        </button>
      </div>

      {result && <AnalysisResult result={result} />}
    </div>
  )
}

export default App