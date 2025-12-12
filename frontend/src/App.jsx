import {useState} from 'react'
import './App.css'

function App() {
    const [text, setText] = useState('')
    const [result, setResult] = useState(null)
    const [loading, setLoading] = useState(false)

    const analyzeDistress = async () => {
        if (!text) return;

        setLoading(true);
        setResult(null);

        try {
            const response = await fetch('http://127.0.0.1:8000/api/signals/entropy', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text}),
            });

            const data = await response.json();
            setResult(data);

        } catch (error) {
            console.error("Error connecting to server:", error);
            alert("Failed to connect to backend");
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score) => {
        if (score < 0.5) return '#4ade80'; // Green
        if (score < 0.7) return '#fbbf24'; // Yellow/Orange
        return '#f87171'; // Red
    };

    return (
        <div className="container" dir="rtl">
            <h1>מעבדת ניתוח אותות</h1>
            <p className="subtitle">
                סביבת ניסוי לבדיקת אלגוריתמים לזיהוי מצוקה (Yagel-Yaakov Platform)
            </p>

            <div className="input-card">
                <textarea
                    className="text-input"
                    rows="5"
                    placeholder="הכנס טקסט לבדיקה כאן... (לדוגמה: 'אני מרגיש תקוע אני מרגיש תקוע')"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    dir="auto"
                />

                <button
                    className="analyze-btn"
                    onClick={analyzeDistress}
                    disabled={loading || text.length < 5}
                >
                    {loading ? 'מעבד נתונים...' : 'נתח טקסט'}
                </button>
            </div>

            {result && (
                <div className="results-container">
                    <h3 style={{textAlign: 'center', marginBottom: '1.5rem', marginTop: 0}}>
                        תוצאות ניתוח:
                    </h3>

                    <div className="results-grid">

                        <div className="meta-box" style={{textAlign: 'right'}}>
                            <div>
                                <span className="label">יחס דחיסה:</span>
                                <strong>{result.metadata.compression_ratio}</strong>
                            </div>
                            <div>
                                <span className="label">זוהתה חזרתיות:</span>
                                <strong>
                                    {result.metadata.is_repetitive ? 'כן ⚠️' : 'לא ✅'}
                                </strong>
                            </div>
                            <div>
                                <span className="label">אורך מקורי:</span>
                                {result.metadata.original_length} תווים
                            </div>
                        </div>

                        <div className="score-box">
                            <span>ציון מצוקה</span>
                            <span
                                className="score-value"
                                style={{
                                    color: getScoreColor(result.score),
                                    direction: 'ltr',
                                    display: 'inline-block'
                                }}
                            >
                                {result.score} <span style={{fontSize: '1rem', color: '#666'}}>/ 1</span>
                            </span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default App