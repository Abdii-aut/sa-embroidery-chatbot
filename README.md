---
title: SA Embroidery Chatbot
emoji: 🧵
colorFrom: green
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# SA Embroidery AI Chatbot

Official AI catalog and sales assistant for **SA Embroidery** ([saembroidery.com](https://saembroidery.com)), built with **FastAPI**, **Groq LLM**, and a responsive frontend widget.

---

## Architecture Overview

- **Backend**: FastAPI (`backend/main.py`) providing:
  - `/chat` endpoint with context injection, intent classification, and fuzzy catalog matching
  - Direct integration with **Groq** (`openai/gpt-oss-20b`)
  - Automated catalog sync from live product API (`https://sa-embroidery-backend.onrender.com/api/read/Products`) with local fallback (`data/knowledge_base.json`)
  - Sliding-window and burst rate-limiting per client IP
  - Serves preview demo at `/` and widget script at `/widget.js`
- **Frontend**: Lightweight vanilla JS widget (`frontend/widget.js`) with modern design, product cards, slideshow, and WhatsApp handoff.

---

## Deployment

### Option 1: Docker (Local / Self-Hosted VPS)

1. Make sure `.env` contains your `GROQ_API_KEY`:
   ```bash
   cp .env.example .env
   # Edit .env and insert your GROQ_API_KEY
   ```

2. Build and launch the container:
   ```bash
   docker compose up -d --build
   ```

3. Verify status:
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

4. Open the chat widget UI at [http://localhost:8000](http://localhost:8000).

To stop the service:
```bash
docker compose down
```

---

### Option 2: Cloud Deployment on Render

This repository includes a `render.yaml` blueprint.

1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/):
   - Click **New +** -> **Blueprint** and connect your GitHub repository (or choose **Web Service** -> Python runtime).
   - Enter your `GROQ_API_KEY` under Environment Variables.
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

---

### Option 3: Local Python Development

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run with Uvicorn:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

3. Visit `http://localhost:8000`.

---

## Embedding the Chatbot on Any Website

Add the following snippet before the closing `</body>` tag on `saembroidery.com` (replace `https://your-chatbot-domain.com` with your deployed URL):

```html
<script>
  window.SA_CHAT_CONFIG = {
    api: 'https://your-chatbot-domain.com/chat',
    productsApi: 'https://sa-embroidery-backend.onrender.com/api/read/Products',
    whatsapp: '923167937030',
    brand: 'SA Embroidery',
    priceCurrency: 'USD',
    site: 'https://saembroidery.com'
  };
</script>
<script src="https://your-chatbot-domain.com/widget.js" async></script>
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Groq API Key for LLM completion |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Groq model identifier |
| `PRODUCTS_API` | `https://sa-embroidery-backend...` | Live catalog JSON endpoint |
| `ALLOWED_ORIGINS` | `https://saembroidery.com,...` | CORS allowed origins (comma-separated) |
| `RATE_LIMIT_PER_MINUTE` | `20` | Max chat requests per minute per IP |
| `RATE_LIMIT_BURST` | `5` | Max burst chat requests in 10s window |
| `REFRESH_SECONDS` | `600` | Periodic catalog sync interval in seconds |
| `PORT` | `8000` | HTTP listening port |