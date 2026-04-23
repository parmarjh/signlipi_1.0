import React, { useState } from 'react'
import Webcam from './components/Webcam'
import BraillePanel from './components/BraillePanel'
import BCIPanel from './components/BCIPanel'
import Chat from './components/Chat'
import { composeSentence, correctText } from './api'

export default function App() {
  const [mode, setMode] = useState('ASL')
  const [running, setRunning] = useState(true)
  const [lastResult, setLastResult] = useState(null)
  const [sentence, setSentence] = useState('')
  const [composed, setComposed] = useState('')
  const [tab, setTab] = useState('sign')

  function handleResult(r) {
    setLastResult(r)
    if (typeof r.sentence === 'string') setSentence(r.sentence)
  }

  async function doCompose() {
    if (!sentence) return
    const tokens = mode === 'ASL' ? sentence.split('') : sentence.split(' ')
    try {
      const r = await composeSentence(tokens, mode)
      setComposed(r.sentence)
    } catch (e) { setComposed(`⚠ ${e.message}`) }
  }

  async function doCorrect() {
    if (!sentence) return
    try {
      const r = await correctText(sentence)
      setComposed(r.output)
    } catch (e) { setComposed(`⚠ ${e.message}`) }
  }

  function reset() { setSentence(''); setComposed('') }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="dot" />
          SignLipi <span style={{ color: 'var(--muted)', fontWeight: 400, marginLeft: 6 }}>
            Sign Language & Brain Lipi Translator
          </span>
        </div>
        <div className="tabs">
          <div className={`tab ${tab === 'sign' ? 'active' : ''}`} onClick={() => setTab('sign')}>Sign</div>
          <div className={`tab ${tab === 'braille' ? 'active' : ''}`} onClick={() => setTab('braille')}>Braille</div>
          <div className={`tab ${tab === 'bci' ? 'active' : ''}`} onClick={() => setTab('bci')}>BCI</div>
        </div>
      </header>

      <div className="content">
        <div className="grid">
          <div className="card" style={{ display: tab === 'sign' ? 'block' : 'none' }}>
            <h3>Sign Language → Text</h3>
            <div className="row" style={{ marginBottom: 10 }}>
              <select value={mode} onChange={e => setMode(e.target.value)}>
                <option value="ASL">ASL (American)</option>
                <option value="ISL">ISL (Indian)</option>
              </select>
              <button className="btn secondary" onClick={() => setRunning(r => !r)}>
                {running ? 'Pause' : 'Resume'}
              </button>
              <button className="btn secondary" onClick={reset}>Clear</button>
              {lastResult?.label && (
                <span className="badge ok">
                  {lastResult.label} · {(lastResult.confidence * 100).toFixed(0)}%
                </span>
              )}
            </div>
            <Webcam mode={mode} running={running} onResult={handleResult} />
            <div style={{ marginTop: 12 }}>
              <div className="badge">Live sentence buffer</div>
              <div className="output big">{sentence || '—'}</div>
              <div className="row" style={{ marginTop: 8 }}>
                <button className="btn" onClick={doCompose}>Compose sentence (GenAI)</button>
                <button className="btn secondary" onClick={doCorrect}>Fix grammar</button>
              </div>
              {composed && (
                <div className="output" style={{ marginTop: 8 }}>{composed}</div>
              )}
            </div>
          </div>

          {tab === 'braille' && (
            <BraillePanel text={sentence || composed} onTextChange={setSentence} />
          )}

          {tab === 'bci' && (
            <BCIPanel onIntent={(intent) => setSentence(s => (s ? s + ' ' : '') + intent)} />
          )}

          <Chat seed={composed || sentence} />
        </div>
      </div>
    </div>
  )
}
