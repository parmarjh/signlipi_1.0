import React, { useState } from 'react'
import { chat } from '../api'

export default function Chat({ seed }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  async function send(text) {
    const q = (text ?? input).trim()
    if (!q) return
    const next = [...messages, { role: 'user', content: q }]
    setMessages(next); setInput(''); setBusy(true)
    try {
      const r = await chat(next)
      setMessages([...next, { role: 'assistant', content: r.reply }])
    } catch (e) {
      setMessages([...next, { role: 'assistant', content: `⚠ ${e.message}` }])
    } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <h3>GenAI Assistant (Ollama, local)</h3>
      <div className="chat">
        {messages.length === 0 && (
          <div className="msg assistant">
            Hi — I can turn your signs/Braille/BCI intents into sentences, fix grammar, or just chat.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>{m.content}</div>
        ))}
        {busy && <div className="msg assistant">…thinking</div>}
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        <input style={{ flex: 1 }} value={input} onChange={e => setInput(e.target.value)}
          placeholder="Ask anything, or hit Compose to send current sentence"
          onKeyDown={e => e.key === 'Enter' && send()} />
        <button className="btn" onClick={() => send()}>Send</button>
        {seed && <button className="btn secondary" onClick={() => send(seed)}>Compose</button>}
      </div>
    </div>
  )
}
