import React, { useState } from 'react';

/**
 * AnalysisResult Component - Dark Dashboard Theme
 * -----------------------------------------------
 * Designed for dark-mode applications. Uses a grid layout to save space
 * and dark backgrounds to reduce eye strain.
 */
const AnalysisResult = ({ result }) => {
    const [detailsPage, setDetailsPage] = useState(false);

    // Helper: Severity Colors (Adjusted for Dark Mode contrast)
    const getScoreColor = (score) => {
        if (score < 0.4) return '#4ade80'; // Bright Green
        if (score < 0.7) return '#facc15'; // Bright Yellow
        return '#f87171'; // Bright Red
    };

    const wmd = result.signals?.semantic_wmd;
    const entropy = result.signals?.entropy;
    const acoustic = result.signals?.acoustic;
    const typing = result.signals?.typing_latency;

    const isRepetitive = entropy?.metadata?.is_repetitive;
    const isSegmentMode = Array.isArray(wmd?.metadata?.segment_scores) && wmd.metadata.segment_scores.length > 0;
    const topicWeights = wmd?.metadata?.topic_weights || {};
    const topicLabels = wmd?.metadata?.topic_labels || {};
    const hasCritical = !!wmd?.metadata?.has_critical_alert;

    // -- Insights Logic --
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

    // -- Visual Components --

    const CircularGauge = ({ value = 0 }) => {
        const size = 110;
        const radius = 45;
        const stroke = 8;
        const center = size / 2;
        const circumference = 2 * Math.PI * radius;
        const clamped = Math.max(0, Math.min(1, Number(value)));
        const offset = circumference * (1 - clamped);

        let statusText = "תקין";
        let statusColor = "#9ca3af"; // Gray
        if (clamped >= 0.7) { statusText = "גבוה"; statusColor = "#f87171"; }
        else if (clamped >= 0.4) { statusText = "בינוני"; statusColor = "#facc15"; }

        return (
            <div style={{ position: 'relative', width: size, height: size, margin: '0 auto' }}>
                <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
                    {/* Background Ring (Darker for dark theme) */}
                    <circle cx={center} cy={center} r={radius} stroke="#374151" strokeWidth={stroke} fill="none" />
                    {/* Colored Value Ring */}
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
                </svg>
                <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#f3f4f6' }}>{Math.round(clamped * 100)}%</span>
                    <span style={{ fontSize: '0.8rem', color: statusColor }}>{statusText}</span>
                </div>
            </div>
        );
    };

    const renderAcousticBar = () => {
        const dist = acoustic?.metadata?.distribution;
        if (!dist) return null;
        return (
            <div style={{ height: 10, borderRadius: 5, overflow: 'hidden', display: 'flex', width: '100%', backgroundColor: '#374151', marginTop: 8 }}>
                <div style={{ width: `${(dist.whisper || 0) * 100}%`, backgroundColor: '#60a5fa' }} title="לחישה" />
                <div style={{ width: `${(dist.normal || 0) * 100}%`, backgroundColor: '#9ca3af' }} title="רגיל" />
                <div style={{ width: `${(dist.shout || 0) * 100}%`, backgroundColor: '#f87171' }} title="צעקה" />
            </div>
        );
    };

    const explainRow = (row) => {
        if (row.critical_alert) return '⚠️ זוהה ביטוי המעיד על סכנה מיידית';
        if (row.method === 'neutral') return 'תוכן יומיומי (ללא סימני מצוקה)';

        const uniqueTopics = (row.matched || [])
            .map(m => topicLabels[m.topic || m.concept_id] || (m.topic || m.concept_id))
            .filter((v, i, a) => a.indexOf(v) === i);

        const parts = [];
        if (uniqueTopics.length) parts.push(`נושאים: ${uniqueTopics.slice(0, 3).join(', ')}`);
        if (row.intensity_he) parts.push(`טון: ${row.intensity_he}`);

        return parts.join(' • ') || 'לא נמצאו חריגות';
    };

    // -- Page 2: Detailed Breakdown --
    if (detailsPage && isSegmentMode) {
        return (
            <div className="results-container" style={{ paddingTop: 0 }}>
                <div className="dark-card header-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                    <h3 style={{ margin: 0, color: '#f3f4f6' }}>פירוט מלא: ניתוח לפי משפטים</h3>
                    <button className="toggle-btn" onClick={() => setDetailsPage(false)}>חזרה לסיכום</button>
                </div>

                <div className="segment-list">
                    {segmentScores.map((row) => (
                        <div key={row.index} className="dark-card seg-card" dir="rtl" style={{ borderRight: `4px solid ${getScoreColor(row.weighted)}` }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                                <span style={{ color: '#e5e7eb', fontSize: '1rem' }}>"{row.snippet}"</span>
                                <span style={{ color: getScoreColor(row.weighted), fontWeight: 'bold' }}>{Math.round(row.weighted * 100)}%</span>
                            </div>

                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                {(row.matched || [])
                                    .filter((v, i, a) => a.findIndex(t => (t.topic || t.concept_id) === (v.topic || v.concept_id)) === i)
                                    .slice(0, 3)
                                    .map((m, i) => {
                                        const id = m.topic || m.concept_id;
                                        const label = topicLabels[id] || id;
                                        return (
                                            <span key={i} className="chip-dark">{label}</span>
                                        )
                                    })}
                                {row.critical_alert && (
                                    <span className="chip-dark critical">סכנה מיידית</span>
                                )}
                            </div>

                            <div style={{ marginTop: 8, fontSize: '0.85rem', color: '#9ca3af' }}>
                                {explainRow(row)}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // -- Page 1: Dark Dashboard Summary --
    return (
        <div className="results-container" dir="rtl">

            {/* 1. Main Score Card (Full Width) */}
            <div className="dark-card main-score-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ textAlign: 'right' }}>
                        <h2 style={{ fontSize: '1.2rem', margin: '0 0 5px 0', color: '#f3f4f6' }}>מדד מצוקה משוקלל</h2>
                        <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>ציון משולב של כלל המדדים</div>

                        {hasCritical && (
                            <div style={{ marginTop: 15, padding: '6px 10px', background: 'rgba(248, 113, 113, 0.2)', border: '1px solid #7f1d1d', borderRadius: 6, color: '#fca5a5', fontSize: '0.85rem', display: 'inline-block' }}>
                                <strong> התראה דחופה:</strong> זוהו ביטויים המעידים על סכנה
                            </div>
                        )}
                    </div>
                    <CircularGauge value={result.overall_distress_score} />
                </div>
            </div>

            {/* 2. Grid for Signals (2 Columns) */}
            <div className="dashboard-grid">

                {/* Content Analysis */}
                <div className="dark-card">
                    <strong style={{ display: 'block', color: '#f3f4f6', marginBottom: 4 }}>תוכן ומשמעות</strong>
                    <div className="info-text-dark">זיהוי נושאים קליניים (כגון ייאוש או עצבות).</div>
                    <div style={{ marginTop: 'auto', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>רמת סיכון:</span>
                        <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: getScoreColor(wmd?.score) }}>{wmd?.score ?? 0}</span>
                    </div>
                </div>

                {/* Cognitive Patterns */}
                <div className="dark-card">
                    <strong style={{ display: 'block', color: '#f3f4f6', marginBottom: 4 }}>דפוסים וחזרתיות</strong>
                    <div className="info-text-dark">זיהוי "תקיעות" מחשבתית (רומינציה).</div>
                    <div style={{ marginTop: 'auto', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>סטטוס:</span>
                        {isRepetitive ? (
                            <span className="status-badge warning">חזרתיות גבוהה</span>
                        ) : (
                            <span className="status-badge success">תקין</span>
                        )}
                    </div>
                </div>

                {/* Typing Latency (if available) */}
                {typing && (
                    <div className="dark-card">
                        <strong style={{ display: 'block', color: '#f3f4f6', marginBottom: 4 }}>דפוסי הקלדה</strong>
                        <div className="info-text-dark">זיהוי היסוס ועיכובים חריגים בהקלדה.</div>
                        <div style={{ marginTop: 'auto', paddingTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                            <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>הפסקות ארוכות:</span>
                            <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: getScoreColor(typing.score) }}>
                                {typing.metadata?.long_pauses_count || 0}
                            </span>
                        </div>
                    </div>
                )}

                {/* Acoustic Analysis (Full width if present) */}
                {acoustic && (
                    <div className="dark-card full-width">
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                            <strong style={{ color: '#f3f4f6' }}>ניתוח קולי</strong>
                            <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>{(acoustic.score * 100).toFixed(0)}% חריגה</span>
                        </div>
                        {renderAcousticBar()}
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280', marginTop: 4 }}>
                            <span>לחישה</span>
                            <span>רגיל</span>
                            <span>צעקה</span>
                        </div>
                    </div>
                )}

            </div>

            {/* 3. Insights Section (Full Width) */}
            {isSegmentMode && (
                <div className="dark-card" style={{ marginTop: 16 }}>
                    <div style={{ borderBottom: '1px solid #374151', paddingBottom: 8, marginBottom: 10 }}>
                        <strong style={{ color: '#f3f4f6' }}>תובנות מרכזיות</strong>
                    </div>

                    {/* Topics Chips */}
                    {topTopics.length > 0 && (
                        <div style={{ marginBottom: 12 }}>
                            {topTopics.map((t, i) => (
                                <span key={i} className="chip-dark" style={{ marginRight: 0, marginLeft: 6 }}>
                  {topicLabels[t] || t}
                </span>
                            ))}
                        </div>
                    )}

                    {/* Top Warning Sentences */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {topSegments.map((s) => (
                            <div key={s.index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.05)', padding: '8px', borderRadius: 6 }}>
                <span style={{ fontSize: '0.9rem', color: '#d1d5db', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', marginLeft: 10 }}>
                  "{s.snippet}"
                </span>
                                <span style={{ fontWeight: 'bold', color: getScoreColor(s.weighted), fontSize: '0.9rem' }}>
                  {s.weighted}
                </span>
                            </div>
                        ))}
                    </div>

                    <button className="toggle-btn dark" onClick={() => setDetailsPage(true)}>
                        לצפייה בפירוט המלא
                    </button>
                </div>
            )}
        </div>
    );
};

export default AnalysisResult;