# LangBridge

LangBridge is a South Indian language learning app with AI-powered pronunciation feedback, gamified lessons, and a personalized learning path. Learn Kannada, Tamil, Telugu, Malayalam, Tulu, and Kodava through interactive practice, streaks, and an in-app AI tutor.

## Features

- **AI speech recognition** — Record yourself speaking and get real-time pronunciation feedback powered by Whisper
- **Text-to-speech** — Listen to native pronunciations before you practice
- **Gamified learning** — Earn XP, maintain streaks, complete daily quests, and climb the leaderboard
- **Adaptive curriculum** — Structured lesson paths with spaced repetition (SRS) for long-term retention
- **AI chatbot** — Ask questions about grammar, vocabulary, and culture (powered by Google Gemini)
- **Custom lessons** — Generate topic-specific phrases on demand
- **Shop & cosmetics** — Spend gems on streak freezes and profile borders
- **Dark / light mode** — Theme toggle across the app

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 19, Vite, React Router, Tailwind CSS, Framer Motion, Chart.js |
| Backend | [Convex](https://convex.dev) (database, real-time sync, server functions) |
| Speech service | Python, Flask, faster-whisper, gTTS |
| AI | Google Gemini (`@google/genai`) |

## Project Structure

```
lang123/
├── src/                  # React frontend
│   ├── pages/            # Route pages (Dashboard, Lessons, Practice, etc.)
│   ├── components/       # UI, speech, gamification, chat widgets
│   └── lib/              # Convex client setup
├── convex/               # Convex backend functions & schema
│   ├── schema.js         # Database tables (users, lessons, assessments, …)
│   ├── auth.js           # Signup / login
│   ├── speech.js         # Audio upload & assessment storage
│   ├── gamification.js   # XP, streaks, achievements
│   ├── srs.js            # Spaced repetition scheduling
│   ├── chatbot.js        # RAG-powered AI tutor
│   └── ai.js             # Custom lesson generation
└── python-service/       # Local speech API (port 5000)
    ├── main.py           # /assess and /tts endpoints
    ├── whisper_service.py
    └── pronunciation.py
```

## Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- A [Convex](https://convex.dev) account
- A [Google AI Studio](https://aistudio.google.com/) API key (for Gemini features)

## Getting Started

### 1. Install frontend dependencies

```bash
npm install
```

### 2. Set up Convex

```bash
npx convex dev
```

This creates a Convex project (if needed), writes `VITE_CONVEX_URL` to `.env.local`, and starts the Convex dev server.

Set your Gemini API key in the Convex dashboard or via CLI:

```bash
npx convex env set GEMINI_API_KEY your_api_key_here
```

### 3. Set up the Python speech service

```bash
cd python-service
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

The speech service runs at `http://localhost:5000` and provides:

- `POST /assess` — Transcribe audio and score pronunciation accuracy
- `POST /tts` — Generate spoken audio for a phrase

> **Note:** The first run downloads the Whisper model, which may take a few minutes.

### 4. Seed lesson data (optional)

With Convex running, populate the lessons table:

```bash
npx convex run seedLessons:seed
```

### 5. Start the frontend

In a separate terminal from the project root:

```bash
npm run dev
```

Open the URL shown in the terminal (typically `http://localhost:5173`).

## Environment Variables

| Variable | Where | Description |
|----------|-------|-------------|
| `VITE_CONVEX_URL` | `.env.local` (auto-generated) | Convex deployment URL for the React client |
| `GEMINI_API_KEY` | Convex environment | Google Gemini API key for chatbot & custom lessons |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npx convex dev` | Start Convex dev server & sync functions |
| `npx convex run seedLessons:seed` | Seed the lessons database |

## Supported Languages

- Kannada
- Tamil
- Telugu
- Malayalam
- Tulu
- Kodava

## License

Private project — not licensed for public distribution.
