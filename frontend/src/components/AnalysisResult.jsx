import React from 'react';

const AnalysisResult = ({result}) => {
    const getScoreColor = (score) => {
        if (score < 0.4) return '#4ade80'; // Green
        if (score < 0.7) return '#fbbf24'; // Yellow
        return '#f87171'; // Red
    };

    const wmd = result.signals?.semantic_wmd;
    const entropy = result.signals?.entropy;
    const isRepetitive = entropy?.metadata?.is_repetitive;

    return (
        <div className="results-container">
            <div className="score-box">
                <span style={{fontSize: '1.2rem'}}>מדד מצוקה משוקלל</span>
                <span className="score-value" style={{color: getScoreColor(result.overall_distress_score)}}>
                    {result.overall_distress_score}
                </span>
            </div>

            <div className="results-grid" style={{marginTop: '20px'}}>
                <div className="meta-box">
                    <strong>ניתוח סמנטי (WMD):</strong>
                    <span>ציון סופי: {wmd?.score}</span>
                    <span>דימיון וקטורי (Base): {wmd?.metadata?.base_score || 0}</span>
                    <span style={{
                        color: wmd?.metadata?.intensity_zone === "Normal" ? "#9ca3af" : "#f87171",
                        fontWeight: 'bold'
                    }}>
                        מצב: {wmd?.metadata?.intensity_zone}
                    </span>
                </div>

                <div className="meta-box">
                    <strong>ניתוח קוגניטיבי (Entropy):</strong>
                    <span>חזרתיות: {isRepetitive ? "⚠️ זיהוי רומינציה" : "✅ תקין"}</span>
                    <span>ציון: {entropy?.score}</span>
                </div>
            </div>
        </div>
    );
};

export default AnalysisResult;