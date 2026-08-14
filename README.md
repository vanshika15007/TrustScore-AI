# TrustScore AI

A machine learning-powered website analysis platform that evaluates trustworthiness through intelligent security assessment, content analysis, and risk profiling.

**Live:** https://trustscore-ai.netlify.app

---

## Overview

TrustScore AI analyzes websites to determine trustworthiness by combining multiple evaluation vectors including security headers, SSL/TLS validation, content sentiment analysis, and malicious pattern detection. The platform processes website data through a fine-tuned BERT model to generate comprehensive trust metrics.

## Architecture

### Frontend Stack
- **React 19** - Component-based UI framework
- **Vite** - High-performance build tool
- **Framer Motion** - Animation library
- **Recharts** - Composable charting
- **Axios** - HTTP client

### Backend Stack
- **FastAPI** - Async Python framework
- **Uvicorn** - ASGI server
- **BeautifulSoup4** - HTML parsing
- **Transformers** - NLP models (BERT)
- **Redis** - Caching layer

### Infrastructure
- **Frontend:** Netlify
- **Backend:** Render  
- **Version Control:** GitHub
- **Runtime:** Python 3.9+, Node.js 18+

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git

### Local Development

**Clone:**
```bash
git clone https://github.com/vanshika15007/TrustScore-AI.git
cd TrustScore-AI
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`

**Backend** (new terminal):
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload
```
Runs on `http://localhost:8000`

## API & Endpoints

### Available Endpoints
- `POST /analyze` - Initiate website analysis
- `GET /status/{task_id}` - Retrieve analysis status
- `GET /health` - Health check

Full API documentation available at `/docs` when running locally.

---

## Environment Configuration

**Frontend (.env):**
```
VITE_API_BASE_URL=https://trustscore-ai-fv8a.onrender.com
```

**Backend (.env):**
```
CORS_ALLOW_ORIGINS=https://trustscore-ai.netlify.app
API_KEY=your-api-key
REDIS_URL=redis://localhost:6379
```

---

## Project Structure

```
trustscore/
├── frontend/         # React application
├── backend/          # FastAPI service
├── extension/        # Browser extension
├── netlify.toml      # Netlify config
├── render.yaml       # Render config
└── README.md
```

---

## Deployment

### Netlify (Frontend)
- Base: `frontend`
- Build: `npm run build`
- Publish: `frontend/dist`

### Render (Backend)
- Build: `pip install -r backend/requirements.txt`
- Start: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`

**Production URLs:**
- https://trustscore-ai.netlify.app
- https://trustscore-ai-fv8a.onrender.com

---

## Performance Considerations

- Initial model load: 2-5 seconds
- Cached analysis via Redis
- Average analysis time: 3-8 seconds
- Free tier services may experience startup delays

---

## Contributing

Issues and pull requests welcome. Please open an issue first for substantial changes.

---

## License

MIT License

**GitHub:** https://github.com/vanshika15007/TrustScore-AI