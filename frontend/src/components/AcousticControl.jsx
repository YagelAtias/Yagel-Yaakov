import React from 'react';

const AcousticControl = ({ decibels, setDecibels }) => {
    return (
        <div className="input-group" style={{ marginTop: '20px', textAlign: 'right' }}>
            <label className="label">
                עוצמת קול מזוהה: <strong>{decibels} dB</strong>
                {decibels > 75 && " (צעקה)"}
                {decibels < 40 && " (לחישה)"}
            </label>
            <input
                type="range"
                min="20"
                max="100"
                value={decibels}
                onChange={(e) => setDecibels(e.target.value)}
                className="slider-input"
                style={{ width: '100%', cursor: 'pointer', marginTop: '10px' }}
            />
        </div>
    );
};

export default AcousticControl;