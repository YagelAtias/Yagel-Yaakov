import React, { useState } from 'react';

const AnalysisResult = ({ result }) => {
  const [showSegments, setShowSegments] = useState(false);
  const [detailsPage, setDetailsPage] = useState(false); // dedicated full-width details view
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
  const isVectorBased = !!wmd?.metadata?.is_vector_based;
  const topicWeights = wmd?.metadata?.topic_weights || {};
  const topicLabels = wmd?.metadata?.topic_labels || {};
  const hasCritical = !!wmd?.metadata?.has_critical_alert;

  // Build insights: top 3 contributing segments and top topics among them
  const segmentScores = isSegmentMode ? [...wmd.metadata.segment_scores] : [];
  const topSegments = segmentScores
    .sort((a, b) => (b?.weighted ?? 0) - (a?.weighted ?? 0))
    .slice(0, 3);
  const topicCount = {};
  topSegments.forEach(s => (s.matched || []).forEach(m => {
    const t = m.topic || m.concept_id;
    if (!t) return;
    topicCount[t] = (topicCount[t] || 0) + 1;
  }));
  const topTopics = Object.entries(topicCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([t]) => t);

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

  // Build a short explanation per segment (day-to-day wording)
  const explainRow = (row) => {
    // Critical alert
    if (row.critical_alert) {
      return 'ייתכן ויש כוונה לפגיעה עצמית, יש צורך בהתייחסות מיידית!';
    }
    // Neutral segment
    if (row.method === 'neutral') {
      return 'מקטע נטרלי, לא נמצאה התאמה משמעותית לנושאים קליניים.';
    }
    // Topics explanation
    const topics = (row.matched || [])
      .slice(0, 2)
      .map(m => topicLabels[m.topic || m.concept_id] || (m.topic || m.concept_id));
    const topicsText = topics.length ? `נושאים מזוהים: ${topics.join(', ')}` : 'אין נושאים חזקים';
    // Intensity and multiplier
    const intensityText = row.intensity_he ? `עוצמה: ${row.intensity_he}` : '';
    // Base vs weighted
    const baseText = typeof row.base === 'number' && row.base !== row.weighted ? `הוגבר מ-${row.base} לפי העוצמה` : '';
    // Build
    return [topicsText, intensityText, baseText].filter(Boolean).join(' · ');
  };

  // Dedicated full-width details page (semantic segments only)
  const renderDetailsPage = () => (
    <div className="results-container" style={{ paddingTop: 16 }}>
      <div className="meta-box" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <strong>פירוט מקטעים</strong>
        <button className="toggle-btn" onClick={() => setDetailsPage(false)}>חזרה לסיכום</button>
      </div>
      <div className="detail-controls" style={{ marginTop: 8 }}>
        <span className="info-text">פירוט ברור לכל מקטע: ציון, נושאים והסבר קצר. אם מוצגת התראה קריטית, המדד הכללי הודגש לצורך תשומת לב.</span>
      </div>
      <div className="segment-cards">
        {segmentScores.map((row) => (
          <div key={row.index} className="seg-card" dir="rtl">
            <div className="seg-head">
              <div className="seg-title" title={row.snippet}>
                משפט זה נאמר ב{row.intensity_he || row.intensity}: {row.snippet}
              </div>
              <div className="seg-score" title={`ציון משוקלל ${row.weighted}`}>{row.weighted}</div>
            </div>
            <div className="seg-topics">
              {(row.matched||[]).slice(0,3).map((m,i)=>{
                const id = m.topic || m.concept_id;
                const label = topicLabels[id] || id;
                return <span key={i} className="chip topic" title={`התאמה ל${label}`}>{label}</span>
              })}
              {row.critical_alert && (
                <span className="badge fallback" style={{ marginInlineStart: 8 }}>התראה קריטית</span>
              )}
            </div>
            <div className="info-text" style={{ marginTop: 6 }}>{explainRow(row)}</div>
            <details className="seg-more">
              <summary>פרטים</summary>
              <div className="seg-meta">
                <div className="seg-meta-item">
                  <span className="seg-meta-label">שיטה: </span>
                  <span className="seg-meta-value">{row.method === 'cad_greedy' ? 'ניתוח סמנטי' : row.method === 'keyword_fallback' ? 'התאמת מילות מפתח' : row.method === 'neutral' ? 'נייטרלי' : 'ללא התאמה'}</span>
                </div>
                <div className="seg-meta-item">
                  <span className="seg-meta-label">ציון בסיסי (לפני השפעת עוצמת הקול): </span>
                  <span className="seg-meta-value">{row.base}</span>
                </div>
                <div className="seg-meta-item">
                  <span className="seg-meta-label">קרבה לנושאים קליניים של מצוקה או דיכאון (גבוה = קרוב): </span>
                  <span className="seg-meta-value">{(1 - Number(row.base_distance || 0)).toFixed(2)}</span>
                </div>
                <div className="seg-meta-item">
                  <span className="seg-meta-label">עוצמת קול: </span>
                  <span className="seg-meta-value">{row.intensity_he || row.intensity}</span>
                </div>
              </div>
            </details>
          </div>
        ))}
      </div>
    </div>
  );

  // If details mode is active, only show the semantic details page (hide other analyses)
  if (detailsPage && isSegmentMode) {
    return renderDetailsPage();
  }

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

      {isSegmentMode && (
        <div className="meta-box insights-card">
          <div className="insights-header">
            <strong>התובנות העיקריות נבעו מהניתוח הסמנטי</strong>
            {hasCritical && (
              <span className="badge fallback" title="הודגש לצורך התרעה בדמו">
                התראה קריטית
              </span>
            )}
          </div>
          <div className="insights-body">
            <div className="insights-list">
              {topSegments.map((s) => (
                <div key={s.index} className="insight-row">
                  <span className="insight-left" style={{ flex: 1, justifyContent: 'flex-start' }}>
                    <span className="info-text" style={{ margin: 0 }}>
                      משפט זה נאמר ב{s.intensity_he}: {s.snippet}
                    </span>
                  </span>
                  <span className="insight-right" style={{ gap: 8 }}>
                    {/* Score first */}
                    <span className="insight-score">{s.weighted}</span>
                    {/* Then topics on the right of the score */}
                    {(s.matched || []).slice(0, 2).map((m, i) => {
                      const id = m.topic || m.concept_id;
                      const label = topicLabels[id] || id;
                      const tw = topicWeights[id] ?? 0.5;
                      let bg = '#2a2a2a';
                      if (tw >= 0.85) bg = '#f87171';
                      else if (tw >= 0.7) bg = '#f59e0b';
                      else if (tw >= 0.5) bg = '#fbbf24';
                      return (
                        <span key={i} className="chip topic" style={{ background: bg, color: '#111', border: 'none' }}>
                          {label}
                        </span>
                      );
                    })}
                    {/* Critical badge at the far end */}
                    {s.critical_alert && (
                      <span className="badge fallback" style={{ marginInlineStart: 6 }}>התראה קריטית</span>
                    )}
                  </span>
                </div>
              ))}
              {topTopics.length > 0 && (
                <div className="insight-summary">
                  <span className="summary-label">נושאים מובילים:</span>
                  {topTopics.map((t, i) => (
                    <span key={i} className="chip topic" style={{ background: '#9ca3af', color: '#111', border: 'none' }}>{topicLabels[t] || t}</span>
                  ))}
                </div>
              )}
              {hasCritical && (
                <div className="info-text" style={{ marginTop: 8 }}>
                  זוהתה התראה קריטית במקטע אחד או יותר. לכן הציון הכללי עלה. מומלצת התייחסות מיידית של הצוות.
                </div>
              )}
              <div style={{ marginTop: 10 }} />
            </div>
          </div>
        </div>
      )}

      <div className="results-grid" style={{ marginTop: '20px' }}>
        <div className="meta-box">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <strong>ניתוח סמנטי</strong>
          </div>
          <div className="info-text">עד כמה הטקסט קשור לנושאים קליניים כמו עצבות, ייאוש, עייפות ועוד.</div>
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
              <button className="toggle-btn" onClick={() => setDetailsPage(true)}>הצג פירוט מקטעים</button>
            </div>
          )}
        </div>

        <div className="meta-box">
          <strong>ניתוח קוגניטיבי (Entropy)</strong>
          <div className="info-text">חזרתיות גבוהה בטקסט יכולה להצביע על רומינציה. טקסט קצר מדי לא נותח.</div>
          <span>חזרתיות: {isRepetitive ? '⚠️ זיהוי רומינציה' : '✅ תקין'}</span>
          <span>ציון: {entropy?.score ?? 0}</span>
          {typeof entropy?.metadata?.compression_ratio !== 'undefined' && (
            <span>יחס דחיסה: {entropy.metadata.compression_ratio}</span>
          )}
        </div>

        {acoustic && (
          <div className="meta-box">
            <strong>סיכום עוצמות קול</strong>
            <div className="info-text">סיכום החלוקה של המקטעים לפי לחישה, רגיל או צעקה.</div>
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