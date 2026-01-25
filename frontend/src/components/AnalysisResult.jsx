import React from 'react';

const AnalysisResult = ({ result }) => {
  const getScoreColor = (score) => {
    if (score < 0.4) return '#4ade80'; // Green
    if (score < 0.7) return '#fbbf24'; // Yellow
    return '#f87171'; // Red
  };

  const wmd = result.signals?.semantic_wmd;
  const entropy = result.signals?.entropy;
  const acoustic = result.signals?.acoustic;
  const isRepetitive = entropy?.metadata?.is_repetitive;

  const isSegmentMode = Array.isArray(wmd?.metadata?.segment_scores) && wmd.metadata.segment_scores.length > 0;
  const topicWeights = wmd?.metadata?.topic_weights || {};

  const ProgressBar = ({ value }) => (
    <div className="progress" title={`מדד: ${Math.round(value * 100)}%`}>
      <div
        className="progress-fill"
        style={{ width: `${Math.round(value * 100)}%`, backgroundColor: getScoreColor(value) }}
      />
    </div>
  );

  const renderAcousticBar = () => {
    const dist = acoustic?.metadata?.distribution;
    if (!dist) return null;
    const whisperW = `${Math.round((dist.whisper || 0) * 100)}%`;
    const normalW = `${Math.round((dist.normal || 0) * 100)}%`;
    const shoutW = `${Math.round((dist.shout || 0) * 100)}%`;
    return (
      <div className="stack-bar" title="סיכום עוצמות קול">
        <div className="stack whisper" style={{ width: whisperW }} />
        <div className="stack normal" style={{ width: normalW }} />
        <div className="stack shout" style={{ width: shoutW }} />
      </div>
    );
  };

  const CircularGauge = ({ value = 0 }) => {
    const size = 80;
    const radius = 32;
    const stroke = 8;
    const center = size / 2;
    const circumference = 2 * Math.PI * radius;
    const clamped = Math.max(0, Math.min(1, Number(value)));
    const offset = circumference * (1 - clamped);
    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="gauge">
        <circle cx={center} cy={center} r={radius} stroke="#2b2b2b" strokeWidth={stroke} fill="none" />
        <circle
          cx={center}
          cy={center}
          r={radius}
          stroke={getScoreColor(clamped)}
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${center} ${center})`}
        />
        <text x="50%" y="50%" dominantBaseline="middle" textAnchor="middle" className="gauge-text">
          {Math.round(clamped * 100)}%
        </text>
      </svg>
    );
  };

  return (
    <div className="results-container">
      <div className="score-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '1.2rem' }}>מדד מצוקה משוקלל</span>
            <div>
              <span className="score-value" style={{ color: getScoreColor(result.overall_distress_score) }}>
                {result.overall_distress_score}
              </span>
            </div>
            <ProgressBar value={Number(result.overall_distress_score || 0)} />
          </div>
          <CircularGauge value={Number(result.overall_distress_score || 0)} />
        </div>
      </div>

      <div className="results-grid" style={{ marginTop: '20px' }}>
        <div className="meta-box">
          <strong>ניתוח סמנטי</strong>
          <span>ציון סופי: {wmd?.score ?? 0}</span>

          {!isSegmentMode && (
            <>
              <span>ציון בסיסי: {wmd?.metadata?.base_score ?? 0}</span>
              {wmd?.metadata?.intensity_zone && (
                <span
                  style={{
                    color: wmd?.metadata?.intensity_zone === 'Normal' ? '#9ca3af' : '#f87171',
                    fontWeight: 'bold',
                  }}
                >
                  מצב: {wmd?.metadata?.intensity_zone}
                </span>
              )}
              {wmd?.metadata?.reason && (
                <span style={{ color: '#9ca3af' }}>מצב חלופי: {wmd?.metadata?.reason}</span>
              )}
            </>
          )}

          {isSegmentMode && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontWeight: 'bold', marginBottom: 6 }}>פירוט מקטעים</div>
              <div className="table-wrap">
                <table className="segments-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>עוצמה</th>
                      <th>בסיס</th>
                      <th>משוקלל</th>
                      <th>שיטה</th>
                      <th>התאמות לנושאים</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wmd.metadata.segment_scores.map((row) => (
                      <tr key={row.index}>
                        <td>{row.index}</td>
                        <td>{row.intensity}</td>
                        <td>{row.base}</td>
                        <td style={{ fontWeight: 600 }}>{row.weighted}</td>
                        <td><span className="chip method">{row.method}</span></td>
                        <td>
                          {(row.matched || []).slice(0, 3).map((m, i) => {
                            const tw = topicWeights[m.topic || m.concept_id] ?? 0.5;
                            let bg = '#2a2a2a';
                            if (tw >= 0.85) bg = '#f87171';
                            else if (tw >= 0.7) bg = '#f59e0b';
                            else if (tw >= 0.5) bg = '#fbbf24';
                            return (
                              <span key={i} className="chip topic" style={{ background: bg, color: '#111', border: 'none' }}>
                                {m.topic || m.concept_id}
                              </span>
                            );
                          })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="meta-box">
          <strong>ניתוח קוגניטיבי (Entropy)</strong>
          <span>חזרתיות: {isRepetitive ? '⚠️ זיהוי רומינציה' : '✅ תקין'}</span>
          <span>ציון: {entropy?.score ?? 0}</span>
          {typeof entropy?.metadata?.compression_ratio !== 'undefined' && (
            <span>יחס דחיסה: {entropy.metadata.compression_ratio}</span>
          )}
        </div>

        {acoustic && (
          <div className="meta-box">
            <strong>סיכום עוצמות קול</strong>
            {renderAcousticBar()}
            <div className="legend">
              <span className="legend-item"><i className="box whisper" /> לחישה</span>
              <span className="legend-item"><i className="box normal" /> רגיל</span>
              <span className="legend-item"><i className="box shout" /> צעקה</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResult;