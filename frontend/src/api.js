const BASE = ''

export async function encodeBraille(text) {
  const r = await fetch(`${BASE}/api/braille/encode`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  return r.json()
}
export async function decodeBraille(braille) {
  const r = await fetch(`${BASE}/api/braille/decode`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ braille }),
  })
  return r.json()
}
export async function composeSentence(tokens, mode = 'ASL') {
  const r = await fetch(`${BASE}/api/genai/compose`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tokens, mode }),
  })
  if (!r.ok) throw new Error((await r.json()).detail || 'compose failed')
  return r.json()
}
export async function correctText(text) {
  const r = await fetch(`${BASE}/api/genai/correct`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!r.ok) throw new Error((await r.json()).detail || 'correct failed')
  return r.json()
}
export async function chat(messages) {
  const r = await fetch(`${BASE}/api/genai/chat`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
  if (!r.ok) throw new Error((await r.json()).detail || 'chat failed')
  return r.json()
}
export async function bciMock(kind = 'alpha') {
  const r = await fetch(`${BASE}/api/bci/mock`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, seconds: 2, fs: 250 }),
  })
  return r.json()
}
