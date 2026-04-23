# SignLipi — Sign Language & Brain Lipi Translator

Open-source, fully **local-host** translator for accessibility. Converts:

- **Sign Language** → text (ASL letters + ISL signs) from your webcam
- **Brain Lipi**
  - **Braille** — Grade-1 English, bidirectional text ↔ Unicode Braille
  - **BCI** — EEG band-power → intent (mock + pluggable real hardware)
- Then uses a **local GenAI (Ollama)** to compose grammatical sentences, fix grammar, and chat.

No cloud APIs. Runs on CPU. Everything speaks over a FastAPI backend with a React (Vite) frontend.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              FRONTEND (React + Vite)                 │
│  • Webcam → WebSocket /ws/sign                       │
│  • Landmark overlay   • Live sentence buffer         │
│  • Braille panel      • BCI panel    • GenAI chat    │
└──────────────────────┬──────────────────────────────┘
                       │  WS + REST
┌──────────────────────▼──────────────────────────────┐
│              BACKEND (FastAPI + Python)              │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐   │
│  │ Sign Engine  │ │  Braille     │ │   BCI      │   │
│  │ MediaPipe    │ │  liblouis-   │ │  Band-     │   │
│  │ + rules      │ │  compatible  │ │  power     │   │
│  └──────────────┘ └──────────────┘ └────────────┘   │
│             │             │             │            │
│             └─────────────▼─────────────┘            │
│                  ┌─────────────┐                     │
│                  │  GenAI      │                     │
│                  │  Ollama     │ llama3.2 / phi3 …   │
│                  └─────────────┘                     │
└─────────────────────────────────────────────────────┘
```

## Quick start (native)

Prereqs: Python 3.10+, Node 18+, and [Ollama](https://ollama.com) for the GenAI features.

```bash
# 1. Pull a small local LLM once
ollama pull llama3.2

# 2. One-shot dev script (starts backend on :8000 and frontend on :5173)
bash scripts/run_dev.sh
```

Open `http://localhost:5173`. Grant webcam permission. Form letters with your hand — the live sentence buffer fills as confidence passes the threshold. Press **Compose sentence (GenAI)** to turn the buffer into a natural sentence.

## Quick start (Docker)

```bash
docker compose up --build
docker exec -it signlipi-ollama ollama pull llama3.2
# Frontend: run `npm run dev` in ./frontend, or serve the built /dist behind any static server.
```

## Backend API

| Method | Path                | Purpose                                |
|--------|---------------------|----------------------------------------|
| GET    | `/api/health`       | Liveness probe                         |
| WS     | `/ws/sign`          | Stream base64 frames → predictions     |
| POST   | `/api/sign/frame`   | One-shot frame classification          |
| POST   | `/api/sign/upload`  | Upload an image file                   |
| POST   | `/api/braille/encode` | Text → Unicode Braille + dot grid    |
| POST   | `/api/braille/decode` | Braille → text                       |
| POST   | `/api/bci/classify` | Classify raw EEG samples               |
| POST   | `/api/bci/mock`     | Generate + classify a mock EEG burst   |
| POST   | `/api/genai/compose`| Tokens → natural sentence              |
| POST   | `/api/genai/correct`| Grammar/spelling fix                   |
| POST   | `/api/genai/chat`   | Free chat with the assistant           |

Interactive docs at `http://localhost:8000/docs`.

## Supported signs (out of the box)

- **ASL letters:** A B C D I L O V W Y (rule-based starter set — easy to extend)
- **ISL signs:** hello, namaste, yes, no, peace, friend

To add signs, edit `backend/app/services/sign_engine.py → RuleSignClassifier`. For production accuracy, train a small MLP on MediaPipe landmarks and load it into `models/`.

## Plugging real BCI hardware

Anywhere you have raw EEG samples (list of floats per channel), POST them to `/api/bci/classify` with the sampling rate. Integrations welcome:

- **BrainFlow** — cross-device, ships with `brainflow.BoardShim` (OpenBCI, Muse, Neurosity…)
- **pylsl** — Lab Streaming Layer
- **Muse-LSL** — easy Muse 2 streaming

Replace `BandPowerClassifier` in `backend/app/services/bci.py` with your trained model for better accuracy.

## Project layout

```
signlipi/
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI entry
│   │   ├── config.py        Settings (env-driven)
│   │   ├── routers/         health, sign_ws, braille, bci, genai
│   │   └── services/        sign_engine, braille, bci, genai
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/      Webcam, BraillePanel, BCIPanel, Chat
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
├── scripts/run_dev.sh
└── README.md
```

## Roadmap

- [ ] Train a learned sign classifier (MLP on MediaPipe landmarks) — drop-in replacement
- [ ] Dynamic gestures (word-level ISL) via a sequence model (GRU / Transformer)
- [ ] Grade-2 English Braille contractions via `liblouis`
- [ ] Full BrainFlow adapter + calibration wizard
- [ ] Voice output (Piper TTS, local)
- [ ] Electron packaging for one-click desktop install

## License

MIT — do whatever helps accessibility. PRs welcome.
