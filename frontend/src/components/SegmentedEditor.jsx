import React, { useState } from 'react';

// Helper to split text into sentences by simple punctuation and new lines
const splitToSentences = (text) => {
  if (!text) return [];
  // Split on ., !, ?, or newline, while keeping Hebrew intact
  const parts = text
    .split(/(?<=[\.!?\n])\s+/)
    .map(t => t.replace(/[\n]/g, ' ').trim())
    .filter(Boolean);
  return parts;
};

const intensityOptions = [
  { value: 'whisper', label: 'לחישה', weight: 300 },
  { value: 'normal', label: 'רגיל', weight: 500 },
  { value: 'shout', label: 'צעקה', weight: 800 },
];

const SegmentedEditor = ({ segments, setSegments }) => {
  const [bulkText, setBulkText] = useState('');

  const handleSplit = () => {
    const sentences = splitToSentences(bulkText);
    const next = sentences.map((s) => ({ text: s, intensity: 'normal' }));
    setSegments(next);
  };

  const updateSegment = (idx, key, value) => {
    const copy = [...segments];
    copy[idx] = { ...copy[idx], [key]: value };
    setSegments(copy);
  };

  const removeSegment = (idx) => {
    setSegments(segments.filter((_, i) => i !== idx));
  };

  return (
    <div className="editor-card" dir="rtl">
      <div className="toggle-row">
        <label className="label">הדבק טקסט וחלק למשפטים</label>
        <button className="remove-btn" onClick={handleSplit}>פצל למשפטים</button>
      </div>
      <textarea
        className="text-input"
        rows={4}
        value={bulkText}
        onChange={(e) => setBulkText(e.target.value)}
        placeholder="הדבק כאן טקסט לפיצול למשפטים"
      />

      <div style={{ marginTop: 12 }}>
        {segments.length === 0 && (
          <div style={{ color: '#9ca3af', marginBottom: 8 }}>אין מקטעים עדיין</div>
        )}

        {segments.map((seg, idx) => {
          const opt = intensityOptions.find(o => o.value === seg.intensity) || intensityOptions[1];
          const fontWeight = opt.weight;
          return (
            <div key={idx} className="segment-row">
              <input
                className="segment-text"
                style={{ fontWeight }}
                value={seg.text}
                onChange={(e) => updateSegment(idx, 'text', e.target.value)}
              />
              <select
                className="segment-select"
                value={seg.intensity}
                onChange={(e) => updateSegment(idx, 'intensity', e.target.value)}
              >
                {intensityOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
              <button className="remove-btn" onClick={() => removeSegment(idx)}>הסר</button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SegmentedEditor;
