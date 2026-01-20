import { useState } from 'react'
import './App.css'
// Importing our new custom components
import AcousticControl from './components/AcousticControl'
import AnalysisResult from './components/AnalysisResult'

function App() {
    const [text, setText] = useState('')
    const [decibels, setDecibels] = useState(60)
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    const analyzeDistress = async () => {
        if (!text) return;
        setLoading(true);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v2/analyze_all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    avg_decibels: parseFloat(decibels)
                }),
            });

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error("Connection error:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container" dir="rtl">
            <h1>מעבדת ניתוח אותות</h1>

            <div className="input-card">
                <label className="label">הכנס טקסט לניתוח כאן:</label>
                <textarea
                    className="text-input"
                    rows="4"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />

                <AcousticControl decibels={decibels} setDecibels={setDecibels} />

                <button className="analyze-btn" onClick={analyzeDistress} disabled={loading}>
                    {loading ? 'מחשב תוצאה משוקללת...' : 'בצע ניתוח'}
                </button>
            </div>

            {result && <AnalysisResult result={result} />}
        </div>
    )
}

export default App