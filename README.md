# 🎙️ Whisper Flow - Enterprise AI Transcription System

![Whisper Flow Banner](https://img.shields.io/badge/Status-Production%20Ready-success?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)
![Python](https://img.shields.io/badge/Backend-Flask%20%2B%20Celery-yellow?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql)

**Whisper Flow Pro** is a self-hosted, enterprise-grade AI transcription platform designed for speed, privacy, and seamless workflow integration. Built on **OpenAI's Whisper models**, it processes audio completely offline using a robust **Asynchronous Microservices Architecture**.

It features a modern **Glassmorphism SPA Dashboard**, real-time processing status, and a **System-Wide Global Hotkey Client** that allows you to dictate into *any* application (Chrome, VS Code, Word) with a single keypress.

---

## ✨ Key Features

### 🚀 **High-Performance AI Engine**
- **Local & Secure:** Runs 100% offline using OpenAI Whisper (Medium/Small models). No data leaves your server.
- **Smart Optimization:** Implements **Anti-Hallucination Filters** to remove silence garbage and repetitive loops.
- **FP32 Fallback:** Optimized for consumer GPUs (GTX 1650/1660) to prevent NaN errors while maintaining speed.
- **Auto-Translation:** Instantly translates Hindi/Hinglish speech into professional English text.

### 🏗️ **Robust Enterprise Architecture**
- **Async Task Queue:** Uses **Celery + Redis** to handle heavy AI workloads in the background without blocking the web server.
- **Scalable Database:** Persists transcription history and logs using **PostgreSQL**.
- **Auto-Cleanup:** Intelligent storage management system that automatically purges processed audio files to save space.

### 💻 **Next-Gen Frontend Experience**
- **Modern UI:** A stunning **Glassmorphism Dashboard** built with **Tailwind CSS** and Vanilla JS.
- **SPA Architecture:** Single Page Application feel with dynamic content loading and real-time polling (no page reloads).
- **Interactive Features:** Animated microphone visualization, one-click copy, and detailed history view.

### 🌐 **Global "Anywhere" Dictation**
- **F4 Hotkey Integration:** A standalone Python client that enables **Global Push-to-Talk**.
- **Auto-Paste Magic:** Records your voice, sends it to the Docker backend, and **automatically pastes** the text into your active window.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend API** | Python, Flask, Gunicorn |
| **AI Processing** | OpenAI Whisper, PyTorch, FFmpeg |
| **Task Queue** | Celery, Redis |
| **Database** | PostgreSQL, SQLAlchemy |
| **Frontend** | HTML5, Tailwind CSS, Vanilla JS (SPA) |
| **Infrastructure** | Docker, Docker Compose |
| **Automation** | Python (`keyboard`, `requests`, `pyaudio`) |

---

## ⚡Whisper-Flow-Enterprise/
├── docker-compose.yml      # Orchestration config
├── Dockerfile              # Container definitions
├── app.py                  # Flask Web Server (API)
├── tasks.py                # Celery Worker (AI Logic)
├── global_client.py        # System-wide Hotkey Client
├── requirements.txt        # Python dependencies
├── start_everything.bat    # One-click launcher
├── templates/
│   └── index.html          # Main Dashboard UI
└── static/
    └── script.js           # Frontend Logic (SPA)

