# SA Embroidery Premium Widget v10

This package updates the **frontend widget only**. Your existing chatbot backend (`/chat`), product API, chat-history handling, product prices and business rules are unchanged.

## Install

1. Back up your existing `frontend/widget.js`.
2. Replace it with the `widget.js` included in this ZIP.
3. Keep `frontend/Sa-Chat-PRO.html` unchanged (it should already include `<script src="widget.js"></script>`).
4. Start FastAPI from your project root: `uvicorn backend.main:app --reload --port 8000`.
5. Visit `http://localhost:8000/frontend/Sa-Chat-PRO.html`, then hard-refresh with Ctrl+Shift+R.

## Updated

- Premium forest-green/charcoal theme with subtle gold detail
- Richer header, status indicator and well-spaced action chips
- Modern, professional welcome card without emojis
- Refined incoming/outgoing messages, product cards, launcher and input
- Mobile layout, keyboard focus states and reduced-motion support
- Existing product price display, AI endpoint and WhatsApp handoff preserved

## Important

Design improvements do not change AI accuracy. Groq integration and catalog consistency must be addressed separately in `backend/main.py`. Do not place your Groq API key in frontend JavaScript.