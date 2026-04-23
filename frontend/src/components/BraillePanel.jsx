import React, { useEffect, useState } from 'react'
import { encodeBraille, decodeBraille } from '../api'

export default function BraillePanel({ text, onTextChange }) {
  const [braille, setBraille] = useState('')
  const [grid, setGrid] = useState([])
  const [reverseIn, setReverseIn] = useState('')
  const [reverseOut, setReverseOut] = useState('')

  useEffect(() => {
    if (!text) { setBraille(''); setGrid([]); return }
    let cancelled = false
    encodeBraille(text).then(r => {
      if (cancelled) return
      setBraille(r.braille); setGrid(r.grid || [])
    })
    return () => { cancelled = true }
  }, [text])

  async function doDecode() {
    const r = await decodeBraille(reverseIn)
    setReverseOut(r.text)
  }

  return (
    <div className="card">
      <h3>Braille (Brain Lipi — Grade 1)</h3>
      <div className="row" style={{ marginBottom: 8 }}>
        <input
          style={{ flex: 1 }}
          value={text}
          onChange={e => onTextChange(e.target.value)}
          placeholder="Type text to convert to Braille"
        />
      </div>
      <div className="output braille">{braille || '—'}</div>
      <div style={{ marginTop: 8 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {grid.map((cell, i) => (
            <svg key={i} width="26" height="38" viewBox="0 0 26 38">
              {cell.map((row, r) => row.map((v, c) => (
                <circle key={`${r}-${c}`} cx={7 + c * 12} cy={6 + r * 9} r="3.2"
                  fill={v ? '#79f1c4' : '#243247'} />
              )))}
            </svg>
          ))}
        </div>
      </div>
      <hr style={{ margin: '14px 0', borderColor: '#243247' }} />
      <h3>Braille → Text</h3>
      <div className="row">
        <input style={{ flex: 1 }} value={reverseIn}
          onChange={e => setReverseIn(e.target.value)}
          placeholder="Paste Braille (⠓⠑⠇⠇⠕)" />
        <button className="btn" onClick={doDecode}>Decode</button>
      </div>
      <div className="output" style={{ marginTop: 8 }}>{reverseOut || '—'}</div>
    </div>
  )
}
