import React, { useEffect, useRef, useState } from 'react'

/**
 * Webcam component: streams frames over a WebSocket to /ws/sign,
 * draws landmark overlays, and raises predictions to the parent.
 */
export default function Webcam({ mode, onResult, running, fps = 8 }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const wsRef = useRef(null)
  const [status, setStatus] = useState('idle')

  useEffect(() => {
    let stream
    let intervalId
    let stopped = false

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 }, audio: false,
        })
        if (stopped) return
        videoRef.current.srcObject = stream
        await videoRef.current.play()

        // Open WS
        const proto = location.protocol === 'https:' ? 'wss' : 'ws'
        const ws = new WebSocket(`${proto}://${location.host}/ws/sign`)
        wsRef.current = ws
        ws.onopen = () => setStatus('connected')
        ws.onclose = () => setStatus('closed')
        ws.onerror = () => setStatus('error')
        ws.onmessage = (ev) => {
          try {
            const data = JSON.parse(ev.data)
            drawLandmarks(data.landmarks || [])
            onResult?.(data)
          } catch {}
        }

        // Throttled capture loop
        const cvs = document.createElement('canvas')
        cvs.width = 320; cvs.height = 240
        const ctx = cvs.getContext('2d')
        intervalId = setInterval(() => {
          if (!running || ws.readyState !== WebSocket.OPEN) return
          ctx.drawImage(videoRef.current, 0, 0, cvs.width, cvs.height)
          const b64 = cvs.toDataURL('image/jpeg', 0.7)
          ws.send(JSON.stringify({ image_b64: b64, mode }))
        }, Math.round(1000 / fps))
      } catch (err) {
        console.error(err); setStatus('camera-denied')
      }
    }
    start()
    return () => {
      stopped = true
      clearInterval(intervalId)
      if (wsRef.current) wsRef.current.close()
      if (stream) stream.getTracks().forEach(t => t.stop())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, running])

  function drawLandmarks(hands) {
    const cvs = canvasRef.current
    const vid = videoRef.current
    if (!cvs || !vid) return
    cvs.width = vid.videoWidth || 640
    cvs.height = vid.videoHeight || 480
    const ctx = cvs.getContext('2d')
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    ctx.strokeStyle = '#79f1c4'
    ctx.fillStyle = '#6ea8ff'
    ctx.lineWidth = 2
    const CONN = [
      [0,1],[1,2],[2,3],[3,4],
      [0,5],[5,6],[6,7],[7,8],
      [5,9],[9,10],[10,11],[11,12],
      [9,13],[13,14],[14,15],[15,16],
      [13,17],[17,18],[18,19],[19,20],[0,17],
    ]
    for (const hand of hands) {
      for (const [a, b] of CONN) {
        const pa = hand[a], pb = hand[b]
        if (!pa || !pb) continue
        ctx.beginPath()
        ctx.moveTo((1 - pa[0]) * cvs.width, pa[1] * cvs.height) // mirror x
        ctx.lineTo((1 - pb[0]) * cvs.width, pb[1] * cvs.height)
        ctx.stroke()
      }
      for (const p of hand) {
        ctx.beginPath()
        ctx.arc((1 - p[0]) * cvs.width, p[1] * cvs.height, 3, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }

  return (
    <div>
      <div className="video-wrap">
        <video ref={videoRef} style={{ transform: 'scaleX(-1)' }} muted playsInline />
        <canvas ref={canvasRef} />
      </div>
      <div className="row" style={{ marginTop: 8 }}>
        <span className={`badge ${status === 'connected' ? 'ok' : 'warn'}`}>
          • stream: {status}
        </span>
        <span className="badge">mode: {mode}</span>
        <span className="badge">{running ? 'capturing' : 'paused'}</span>
      </div>
    </div>
  )
}
