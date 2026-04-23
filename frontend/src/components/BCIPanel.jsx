import React, { useState } from 'react'
import { bciMock } from '../api'

const BANDS = [
  { kind: 'alpha',  label: 'Alpha (yes)',   tone: '#79f1c4' },
  { kind: 'beta',   label: 'Beta (select)', tone: '#6ea8ff' },
  { kind: 'theta',  label: 'Theta (no)',    tone: '#ffd07a' },
  { kind: 'gamma',  label: 'Gamma (help)',  tone: '#ff7ad1' },
]

export default function BCIPanel({ onIntent }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function simulate(kind) {
    setLoading(true)
    try {
      const r = await bciMock(kind)
      setResult(r); onIntent?.(r.intent)
    } finally { setLoading(false) }
  }

  return (
    <div className="card">
      <h3>BCI — Brain signal → Intent</h3>
      <p style={{ color: 'var(--muted)', marginTop: 0 }}>
        Simulated EEG band-power classifier. Plug in OpenBCI / Muse / BrainFlow via the
        <span className="kbd"> /api/bci/classify </span> endpoint.
      </p>
      <div className="grid-4">
        {BANDS.map(b => (
          <button key={b.kind} className="intent-btn" disabled={loading}
            onClick={() => simulate(b.kind)} style={{ borderColor: b.tone }}>
            {b.label}
          </button>
        ))}
      </div>
      {result && (
        <div className="output" style={{ marginTop: 12 }}>
          <strong>Intent:</strong> {result.intent}  ·  confidence {(result.confidence * 100).toFixed(1)}%<br />
          <small style={{ color: 'var(--muted)' }}>
            features: {Object.entries(result.features).map(([k, v]) => `${k}:${v.toFixed(2)}`).join('  ')}
          </small>
        </div>
      )}
    </div>
  )
}
